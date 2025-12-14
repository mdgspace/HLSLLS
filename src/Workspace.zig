const std = @import("std");
const util = @import("util.zig");
const lsp = @import("lsp.zig");
const Spec = @import("Spec.zig");
const parse = @import("parse.zig");
pub const Document = @import("Document.zig");

const Workspace = @This();

allocator: std.mem.Allocator,
arena_state: std.heap.ArenaAllocator.State,
spec: Spec,
builtin_completions: []const lsp.CompletionItem,

documents: std.StringHashMapUnmanaged(*Document) = .{},

pub fn init(allocator: std.mem.Allocator) !@This() {
    var arena = std.heap.ArenaAllocator.init(allocator);
    errdefer arena.deinit();

    const spec = try Spec.load(arena.allocator());
    const builtin_completions = try builtinCompletions(arena.allocator(), &spec);

    return .{
        .allocator = allocator,
        .arena_state = arena.state,
        .spec = spec,
        .builtin_completions = builtin_completions,
    };
}

pub fn deinit(self: *Workspace) void {
    var entries = self.documents.iterator();
    while (entries.next()) |entry| {
        const document = entry.value_ptr.*;
        self.allocator.free(document.path);
        self.allocator.free(document.uri);
        document.deinit();
        self.allocator.destroy(document);
    }
    self.documents.deinit(self.allocator);
    self.arena_state.promote(self.allocator).deinit();
}

pub fn getDocument(self: *Workspace, document: lsp.TextDocumentIdentifier) !?*Document {
    const path = try util.pathFromUri(self.allocator, document.uri);
    defer self.allocator.free(path);
    return self.documents.get(path);
}

pub fn getOrCreateDocument(
    self: *Workspace,
    document: lsp.VersionedTextDocumentIdentifier,
) !*Document {
    const path = try util.pathFromUri(self.allocator, document.uri);
    errdefer self.allocator.free(path);

    const entry = try self.documents.getOrPut(self.allocator, path);
    if (entry.found_existing) {
        self.allocator.free(path);
    } else {
        errdefer self.documents.removeByPtr(entry.key_ptr);

        const new_document = try self.allocator.create(Document);
        errdefer self.allocator.destroy(new_document);

        const uri_clone = try self.allocator.dupe(u8, document.uri);
        errdefer self.allocator.free(uri_clone);

        entry.key_ptr.* = path;
        new_document.* = .{
            .uri = uri_clone,
            .path = path,
            .workspace = self,
            .version = document.version,
        };
        entry.value_ptr.* = new_document;
    }
    return entry.value_ptr.*;
}

pub fn getOrLoadDocument(
    self: *Workspace,
    document: lsp.TextDocumentIdentifier,
) !*Document {
    const path = try util.pathFromUri(self.allocator, document.uri);
    errdefer self.allocator.free(path);

    const entry = try self.documents.getOrPut(self.allocator, path);
    if (entry.found_existing) {
        self.allocator.free(path);
    } else {
        errdefer self.documents.removeByPtr(entry.key_ptr);

        const max_megabytes = 16;
        const contents = try std.fs.cwd().readFileAlloc(self.allocator, path, max_megabytes << 20);
        errdefer self.allocator.free(contents);

        const new_document = try self.allocator.create(Document);
        errdefer self.allocator.destroy(new_document);

        const uri_clone = try self.allocator.dupe(u8, document.uri);
        errdefer self.allocator.free(uri_clone);

        entry.key_ptr.* = path;
        new_document.* = .{
            .uri = uri_clone,
            .path = path,
            .workspace = self,
            .version = null,
            .contents = std.ArrayList(u8).fromOwnedSlice(contents),
        };
        entry.value_ptr.* = new_document;
    }
    return entry.value_ptr.*;
}

fn builtinCompletions(arena: std.mem.Allocator, spec: *const Spec) ![]lsp.CompletionItem {
    var completions = std.ArrayList(lsp.CompletionItem).empty;

    try completions.ensureUnusedCapacity(
        arena,
        spec.types.len + spec.variables.len + spec.functions.len,
    );

    for (spec.types) |typ| {
        try completions.append(arena, .{
            .label = typ.name,
            .kind = .class,
            .documentation = .{
                .kind = .markdown,
                .value = try std.mem.join(arena, "\n\n", typ.description),
            },
        });
    }

    keywords: for (spec.keywords) |keyword| {
        for (spec.types) |typ| {
            if (std.mem.eql(u8, keyword.name, typ.name)) {
                continue :keywords;
            }
        }

        try completions.append(arena, .{
            .label = keyword.name,
            .kind = .keyword,
            .documentation = .{
                .kind = .markdown,
                .value = switch (keyword.kind) {
                    .hlsl => "Available in standard HLSL.",
                    .reserved => "Reserved for future use.",
                },
            },
        });
    }

    for (spec.variables) |variable| {
        var anonymous_signature = std.Io.Writer.Allocating.init(arena);
        try writeVariableSignature(variable, &anonymous_signature.writer, .{ .names = false });

        var named_signature = std.Io.Writer.Allocating.init(arena);
        try writeVariableSignature(variable, &named_signature.writer, .{ .names = true });

        try completions.append(arena, .{
            .label = variable.name,
            .labelDetails = .{ .detail = anonymous_signature.toOwnedSlice() },
            .detail = named_signature.toOwnedSlice(),
            .kind = .variable,
            .documentation = try itemDocumentation(arena, variable),
        });
    }

    for (spec.functions) |function| {
        var anonymous_signature = std.Io.Writer.Allocating.init(arena);
        try writeFunctionSignature(function, &anonymous_signature.writer, .{ .names = false });

        var named_signature = std.Io.Writer.Allocating.init(arena);
        try writeFunctionSignature(function, &named_signature.writer, .{ .names = true });

        try completions.append(arena, .{
            .label = function.name,
            .labelDetails = .{ .detail = anonymous_signature.toOwnedSlice() },
            .kind = .function,
            .detail = named_signature.toOwnedSlice(),
            .documentation = try itemDocumentation(arena, function),
        });
    }

    return completions.toOwnedSlice();
}

fn itemDocumentation(arena: std.mem.Allocator, item: anytype) !lsp.MarkupContent {
    var documentation = std.Io.Writer.Allocating.init(arena);

    for (item.description orelse &.{}) |paragraph| {
        try documentation.writer.write(paragraph);
        try documentation.writer.write("\n\n");
    }

    // if (item.extensions) |extensions| {
    //     try documentation.appendSlice("```hlsl\n");
    //     for (extensions) |extension| {
    //         try documentation.writer().print("#extension {s} : enable\n", .{extension});
    //     }
    //     try documentation.appendSlice("```\n");
    // }

    return .{ .kind = .markdown, .value = try documentation.toOwnedSlice() };
}

fn writeVariableSignature(
    variable: Spec.Variable,
    writer: std.Io.Writer,
    options: struct { names: bool },
) !void {
    if (!std.meta.eql(variable.modifiers, .{})) {
        try writer.print("{f}", .{variable.modifiers});
        try writer.write(" ");
    }

    try writer.write(variable.type);

    if (options.names) {
        try writer.write(" ");
        try writer.write(variable.name);

        if (variable.default_value) |value| {
            try writer.write(" = ");
            try writer.write(value);
        }

        try writer.write(";");
    }
    writer.flush();
}

fn writeFunctionSignature(
    function: Spec.Function,
    writer: std.Io.Writer,
    options: struct { names: bool },
) !void {
    try writer.write(function.return_type);
    try writer.write(" ");
    if (options.names) try writer.write(function.name);
    try writer.write("(");
    for (function.parameters, 0..) |param, i| {
        if (i != 0) try writer.write(", ");
        if (param.optional) try writer.write("[");
        if (param.modifiers) |modifiers| {
            try writer.print("{f}", .{modifiers});
            try writer.write(" ");
        }
        if (options.names) {
            const array_start = std.mem.indexOfScalar(u8, param.type, '[') orelse param.type.len;
            try writer.write(param.type[0..array_start]);
            try writer.write(" ");
            try writer.write(param.name);
            try writer.write(param.type[array_start..]);
        } else {
            try writer.write(param.type);
        }
        if (param.optional) try writer.write("]");
    }
    try writer.write(")");
    writer.flush();
}
