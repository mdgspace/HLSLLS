const std = @import("std");
const lsp = @import("lsp.zig");

var global_allocator: std.mem.Allocator = undefined;
var channel: *std.io.BufferedWriter(4096, @TypeOf(std.io.getStdOut().writer())) = undefined;
var running: bool = true;
var is_initialized: bool = false;
var parent_pid: ?c_int = null;

pub const WriteError = std.fs.File.WriteError || std.net.Stream.WriteError;

var stdin: std.fs.File = std.io.getStdIn();
var stdout: std.fs.File = std.io.getStdOut();

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{ .stack_trace_frames = 8 }){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();
    global_allocator = allocator;

    var buffered_reader = std.io.bufferedReader(stdin.reader());
    var buffered_writer = std.io.bufferedWriter(stdout.writer());
    const reader = buffered_reader.reader();
    channel = &buffered_writer;

    var header_buffer: [1024]u8 = undefined;
    var header_stream = std.io.fixedBufferStream(&header_buffer);

    var content_buffer = std.ArrayList(u8).init(allocator);
    defer content_buffer.deinit();

    var parse_arena = std.heap.ArenaAllocator.init(allocator);
    defer parse_arena.deinit();
 
    const max_content_length = 4 << 20; // 4MB

    outer: while (running) {
        defer _ = parse_arena.reset(.retain_capacity);

        // read headers from stdin
        const headers = blk: {
            header_stream.reset();
            while (!std.mem.endsWith(u8, header_buffer[0..header_stream.pos], "\r\n\r\n")) {
                reader.streamUntilDelimiter(header_stream.writer(), '\n', null) catch |err| {
                    if (err == error.EndOfStream) break :outer;
                    return err;
                };
                _ = try header_stream.write("\n");
            }
            break :blk try parseHeaders(header_buffer[0..header_stream.pos]);
        };

        // read content
        const contents = blk: {
            if (headers.content_length > max_content_length) return error.MessageTooLong;
            try content_buffer.resize(headers.content_length);
            const actual_length = try reader.readAll(content_buffer.items);
            if (actual_length < headers.content_length) return error.UnexpectedEof;
            break :blk content_buffer.items;
        };

        var message = blk: {
            // !!!
            var scanner = std.json.Scanner.initCompleteInput(parse_arena.allocator(), contents);
            break :blk std.json.parseFromTokenSourceLeaky(
                Message(Request),
                parse_arena.allocator(),
                &scanner,
                .{ .allocate = .alloc_if_needed },
            ) catch |err| {
                // logJsonError(@errorName(err), diagnostics, contents);
                fail(.null, .{ .code = .parse_error, .message = @errorName(err) }) catch {};
                continue;
            };
        };

        handleMessage(&message) catch |err| switch (err) {
            error.Failure => continue,
            else => return err,
        };

    }

    // return 0;
}


pub const Dispatch = struct {
    pub const methods = [_][]const u8{
        "initialize",
        "initialized",
        "shutdown",
        "textDocument/didOpen",
        "textDocument/didClose",
        "textDocument/didSave",
        "textDocument/didChange",
        "textDocument/completion",
        "textDocument/hover",
        "textDocument/formatting",
        "textDocument/definition",
    };

    fn parseParams(comptime T: type, request: *Request) !std.json.Parsed(T) {
        return std.json.parseFromValue(T, global_allocator, request.params, .{
            .ignore_unknown_fields = true,
        });
    }

    pub const InitializeParams = struct {
        processId: ?c_int = null,
        clientInfo: ?struct {
            name: []const u8,
            version: ?[]const u8 = null,
        } = null,
        capabilities: lsp.ClientCapabilities,
    };

    pub fn initialize(request: *Request) !void {
        if (is_initialized) {
            return fail(request.id, .{
                .code = .invalid_request,
                .message = "server already initialized",
            });
        }

        const params = try parseParams(InitializeParams, request);
        defer params.deinit();

        try success(request.id, .{
            .capabilities = .{
                .completionProvider = .{
                    .triggerCharacters = .{"."},
                },
                .textDocumentSync = .{
                    .openClose = true,
                    .change = @intFromEnum(lsp.TextDocumentSyncKind.incremental),
                    .willSave = false,
                    .willSaveWaitUntil = false,
                    .save = .{ .includeText = false },
                },
                .hoverProvider = true,
                .documentFormattingProvider = true,
                .definitionProvider = true,
            },
            .serverInfo = .{ .name = "hlslls" },
        });

        is_initialized = true;
        parent_pid = parent_pid orelse params.value.processId;
    }

    pub fn shutdown(request: *Request) !void {
        running = false;
        try success(request.id, null);
    }

    pub fn initialized(request: *Request) !void {
        _ = request;
        return;
    }

    pub const DidOpenParams = struct {
        textDocument: lsp.TextDocumentItem,
    };

    pub fn @"textDocument/didOpen"(request: *Request) !void {
        const params = try parseParams(DidOpenParams, request);
        defer params.deinit();

        const document = &params.value.textDocument;
        std.log.debug("opened: {s} : {s} : {} : {}", .{
            document.uri,
            document.languageId,
            document.version,
            document.text.len,
        });
    }

    pub const DidCloseParams = struct {
        textDocument: lsp.TextDocumentIdentifier,
    };

    pub fn @"textDocument/didClose"(request: *Request) !void {
        const params = try parseParams(DidCloseParams, request);
        defer params.deinit();
        std.log.debug("closed: {s}", .{params.value.textDocument.uri});
    }

    pub const DidSaveParams = struct {
        textDocument: lsp.TextDocumentIdentifier,
        text: ?[]const u8 = null,
    };

    pub fn @"textDocument/didSave"(request: *Request) !void {
        const params = try parseParams(DidSaveParams, request);
        defer params.deinit();

        std.log.debug("saved: {s} : {?}", .{
            params.value.textDocument.uri,
            if (params.value.text) |text| text.len else null,
        });
    }

    pub const DidChangeParams = struct {
        textDocument: lsp.VersionedTextDocumentIdentifier,
        contentChanges: []const lsp.TextDocumentContentChangeEvent,
    };

    pub fn @"textDocument/didChange"(request: *Request) !void {
        const params = try parseParams(DidChangeParams, request);
        defer params.deinit();

        std.log.debug("didChange: {s}", .{params.value.textDocument.uri});
    }

    pub const CompletionParams = struct {
        textDocument: lsp.TextDocumentIdentifier,
        position: lsp.Position,
    };

    pub fn @"textDocument/completion"(request: *Request) !void {
        const params = try parseParams(CompletionParams, request);
        defer params.deinit();

        std.log.debug("complete: {} {s}", .{ params.value.position, params.value.textDocument.uri });
    }
    
    pub const HoverParams = struct {
        textDocument: lsp.TextDocumentIdentifier,
        position: lsp.Position,
    };

    pub fn @"textDocument/hover"(request: *Request) !void {
        const params = try parseParams(HoverParams, request);
        defer params.deinit();

        std.log.debug("hover: {} {s}", .{ params.value.position, params.value.textDocument.uri });
    }

    const FormattingParams = struct {
        textDocument: lsp.TextDocumentIdentifier,
        options: struct {
            tabSize: u32 = 4,
            insertSpaces: bool = true,
        },
    };

    pub fn @"textDocument/formatting"(request: *Request) !void {
        const params = try parseParams(FormattingParams, request);
        defer params.deinit();
        std.log.debug("format: {s}", .{params.value.textDocument.uri});
    }

    const DefinitionParams = struct {
        textDocument: lsp.TextDocumentIdentifier,
        position: lsp.Position,
    };

    pub fn @"textDocument/definition"(request: *Request) !void {
        const params = try parseParams(DefinitionParams, request);
        defer params.deinit();
        std.log.debug("goto definition: {} {s}", .{
            params.value.position,
            params.value.textDocument.uri,
        });
    }
};


fn dispatchRequest(request: *Request) !void {
    if (!std.mem.eql(u8, request.jsonrpc, "2.0"))
        return fail(request.id, .{
            .code = .invalid_request,
            .message = "invalid jsonrpc version",
        });

    std.log.debug("method: '{'}'", .{std.zig.fmtEscapes(request.method)});

    if (!is_initialized and !std.mem.eql(u8, request.method, "initialize"))
        return fail(request.id, .{
            .code = .server_not_initialized,
            .message = "server has not been initialized",
        });

    inline for (Dispatch.methods) |method| {
        if (std.mem.eql(u8, request.method, method)) {
            try @field(Dispatch, method)(request);
            break;
        }
    } else {
        return fail(request.id, .{
            .code = .method_not_found,
            .message = request.method,
        });
    }
}


fn sendResponse(response: *const Response) WriteError!void {
    const format_options = std.json.StringifyOptions{
        .emit_null_optional_fields = false,
    };

    // get the size of the encoded message
    var counting = std.io.countingWriter(std.io.null_writer);
    try std.json.stringify(response, format_options, counting.writer());
    const content_length = counting.bytes_written;

    // send the message to the client
    const writer = channel.writer();
    try writer.print("Content-Length: {}\r\n\r\n", .{content_length});
    try std.json.stringify(response, format_options, writer);
    try channel.flush();
}

pub const Request = struct {
    pub const Id = std.json.Value;

    jsonrpc: []const u8,
    method: []const u8,
    id: Id = .null,
    params: std.json.Value = .null,
};

pub const Response = struct {
    jsonrpc: []const u8 = "2.0",
    id: Request.Id,
    result: Result,

    pub const Result = union(enum) {
        success: JsonPreformatted,
        failure: lsp.Error,
    };

    pub fn jsonStringify(self: @This(), jw: anytype) !void {
        try jw.beginObject();

        try jw.objectField("jsonrpc");
        try jw.write(self.jsonrpc);

        try jw.objectField("id");
        try jw.write(self.id);

        switch (self.result) {
            .success => |data| {
                try jw.objectField("result");
                try jw.write(data);
            },
            .failure => |err| {
                try jw.objectField("error");
                try jw.write(err);
            },
        }

        try jw.endObject();
    }
};

pub fn Message(comptime Inner: type) type {
    return union(enum) {
        single: Inner,
        batch: []Inner,

        pub fn jsonParse(
            allocator: std.mem.Allocator,
            source: anytype,
            options: std.json.ParseOptions,
        ) !@This() {
            _ = allocator;
            switch (try source.peekNextTokenType()) {
                .object_begin => return .{
                    .single = try std.json.innerParse(Inner, global_allocator, source, options),
                },
                .array_begin => return .{
                    .batch = try std.json.innerParse([]Inner, global_allocator, source, options),
                },
                else => return error.UnexpectedToken,
            }
        }
    };
}

const HeaderValues = struct {
    content_length: u32,
    mime_type: []const u8,
};


fn parseHeaders(bytes: []const u8) !HeaderValues {
    var content_length: ?u32 = null;
    var mime_type: []const u8 = "application/vscode-jsonrpc; charset=utf-8";

    var lines = std.mem.splitScalar(u8, bytes, '\n');
    while (lines.next()) |line| {
        const trimmed = std.mem.trimRight(u8, line, &std.ascii.whitespace);
        if (trimmed.len == 0) continue;

        const colon = std.mem.indexOfScalar(u8, trimmed, ':') orelse return error.InvalidHeader;

        const name = trimmed[0..colon];
        const value = std.mem.trim(u8, trimmed[colon + 1 ..], &std.ascii.whitespace);

        if (std.ascii.eqlIgnoreCase(name, "Content-Length")) {
            content_length = try std.fmt.parseInt(u32, value, 10);
        } else if (std.ascii.eqlIgnoreCase(name, "Content-Type")) {
            mime_type = value;
        }
    }

    return HeaderValues{
        .content_length = content_length orelse return error.MissingContentLength,
        .mime_type = mime_type,
    };
}

pub const JsonPreformatted = struct {
    raw: []const u8,

    pub fn jsonStringify(self: @This(), jw: anytype) !void {
        try jw.print("{s}", .{self.raw});
    }
};

pub fn fail(
    id: Request.Id,
    err: lsp.Error,
) (error{Failure} || WriteError) {
    try sendResponse(&.{ .id = id, .result = .{ .failure = err } });
    return error.Failure;
}

pub fn success(id: Request.Id, data: anytype) !void {
    const bytes = try std.json.stringifyAlloc(global_allocator, data, .{});
    defer global_allocator.free(bytes);
    try sendResponse(&Response{ .id = id, .result = .{ .success = .{ .raw = bytes } } });
}

fn handleMessage(message: *Message(Request)) !void {
    switch (message.*) {
        .single => |*request| try dispatchRequest(request),
        .batch => {}
    }
}

