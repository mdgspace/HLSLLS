const std = @import("std");

pub const InitializeResult = struct {
    capabilities: ServerCapabilities,
    serverInfo: ?struct {
        name: []const u8,
        version: ?[]const u8 = null,
    } = null,
};

pub const ClientCapabilities = struct {};

pub const ServerCapabilities = struct {
    completionProvider: CompletionOptions = .{},
    textDocumentSync: TextDocumentSyncOptions = .{},
};

pub const CompletionOptions = struct {
    triggerCharacters: ?[]const []const u8 = null,
};

pub const PositionEncoding = []const u8;

pub const TextDocumentSyncOptions = struct {
    openClose: bool = true,
    change: TextDocumentSyncKind = .full,
};

pub const TextDocumentContentChangeEvent = struct {
    range: ?Range = null,
    text: []const u8,
};

pub const Range = struct {
    start: Position,
    end: Position,

    pub fn format(self: @This(), comptime _: []const u8, _: std.fmt.FormatOptions, writer: anytype) !void {
        try writer.print("{}..{}", .{ self.start, self.end });
    }
};

pub const Position = struct {
    line: u32,
    character: u32,

    pub fn format(self: @This(), comptime _: []const u8, _: std.fmt.FormatOptions, writer: anytype) !void {
        try writer.print("{}:{}", .{ self.line, self.character });
    }
};


pub const TextDocumentSyncKind = enum(u8) {
    none = 0,
    full = 1,
    incremental = 2,

    pub fn jsonStringify(self: @This(), jw: anytype) !void {
        try jw.write(@intFromEnum(self));
    }
};

pub const TextDocumentItem = struct {
    uri: []const u8,
    languageId: []const u8,
    version: i64,
    text: []const u8,

    pub fn versioned(self: @This()) VersionedTextDocumentIdentifier {
        return .{ .uri = self.uri, .version = self.version };
    }
};

pub const TextDocumentIdentifier = struct {
    uri: []const u8,
};

pub const VersionedTextDocumentIdentifier = struct {
    uri: []const u8,
    version: i64,
};

pub const Error = struct {
    code: Code,
    message: []const u8,
    data: ?std.json.Value = null,

    pub const Code = enum(i32) {
        pub fn jsonStringify(self: @This(), jw: anytype) !void {
            try jw.write(@intFromEnum(self));
        }

        pub fn jsonParse(
            allocator: std.mem.Allocator,
            source: anytype,
            options: std.json.ParseOptions,
        ) !@This() {
            const tag = try std.json.innerParse(std.meta.Tag(@This()), allocator, source, options);
            return std.meta.intToEnum(@This(), tag);
        }


        parse_error = -32700,
        invalid_request = -32600,
        method_not_found = -32601,
        invalid_params = -32502,
        internal_error = -32603,

        server_not_initialized = -32002,
        unknown_error_code = -32001,

        request_failed = -32803,
        server_cancelled = -32802,
        content_modified = -32801,
        request_cancelled = -32800,

        _,
    };
};


pub const MarkupContent = struct {
    pub const Kind = enum { plaintext, markdown };

    kind: Kind,
    value: []const u8,
};

