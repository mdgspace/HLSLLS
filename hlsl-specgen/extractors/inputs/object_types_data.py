# extractors/inputs/object_types_data.py
# Exhaustive HLSL object, sampler, texture, and buffer types
# (for inclusion into the Language Server spec)

TYPES = [
    # ------------------------------------------------------------------------
    # SAMPLERS
    # ------------------------------------------------------------------------
    {"name": "SamplerState",
        "description": ["sampler state object"]},
    {"name": "SamplerComparisonState",    "description": [
        "comparison sampler state object"]},

    # ------------------------------------------------------------------------
    # TEXTURES (sampled resources)
    # ------------------------------------------------------------------------
    {"name": "Texture1D",
        "description": ["1D sampled texture"]},
    {"name": "Texture1DArray",            "description": [
        "array of 1D sampled textures"]},
    {"name": "Texture2D",
        "description": ["2D sampled texture"]},
    {"name": "Texture2DArray",            "description": [
        "array of 2D sampled textures"]},
    {"name": "Texture3D",
        "description": ["3D sampled texture"]},
    {"name": "TextureCube",
        "description": ["cube sampled texture"]},
    {"name": "TextureCubeArray",          "description": [
        "array of cube sampled textures (SM 4.1+)"]},
    {"name": "Texture2DMS",               "description": [
        "2D multisample texture"]},
    {"name": "Texture2DMSArray",          "description": [
        "array of 2D multisample textures"]},

    # ------------------------------------------------------------------------
    # READ/WRITE TEXTURES (UAVs)
    # ------------------------------------------------------------------------
    {"name": "RWTexture1D<T>",
        "description": ["typed 1D UAV texture"]},
    {"name": "RWTexture1DArray<T>",       "description": [
        "typed 1D array UAV texture"]},
    {"name": "RWTexture2D<T>",
        "description": ["typed 2D UAV texture"]},
    {"name": "RWTexture2DArray<T>",       "description": [
        "typed 2D array UAV texture"]},
    {"name": "RWTexture3D<T>",
        "description": ["typed 3D UAV texture"]},

    # ------------------------------------------------------------------------
    # BUFFERS (typed)
    # ------------------------------------------------------------------------
    {"name": "Buffer<T>",                 "description": [
        "read-only typed buffer"]},
    {"name": "RWBuffer<T>",               "description": [
        "read-write typed buffer"]},

    # ------------------------------------------------------------------------
    # STRUCTURED BUFFERS
    # ------------------------------------------------------------------------
    {"name": "StructuredBuffer<T>",       "description": [
        "read-only structured buffer"]},
    {"name": "RWStructuredBuffer<T>",     "description": [
        "read-write structured buffer"]},
    {"name": "AppendStructuredBuffer<T>", "description": [
        "append-only structured buffer"]},
    {"name": "ConsumeStructuredBuffer<T>", "description": [
        "consume-only structured buffer"]},

    # ------------------------------------------------------------------------
    # BYTE-ADDRESS BUFFERS
    # ------------------------------------------------------------------------
    {"name": "ByteAddressBuffer",         "description": [
        "raw byte-address buffer (read-only)"]},
    {"name": "RWByteAddressBuffer",       "description": [
        "raw byte-address buffer (read-write)"]},

    # ------------------------------------------------------------------------
    # RASTERIZER-ORDERED VIEWS (ROVs)
    # ------------------------------------------------------------------------
    {"name": "RasterizerOrderedBuffer<T>",
        "description": ["rasterizer-ordered typed buffer"]},
    {"name": "RasterizerOrderedStructuredBuffer<T>",
        "description": ["rasterizer-ordered structured buffer"]},
    {"name": "RasterizerOrderedByteAddressBuffer",
        "description": ["rasterizer-ordered byte-address buffer"]},
    {"name": "RasterizerOrderedTexture1D<T>",
        "description": ["rasterizer-ordered 1D UAV texture"]},
    {"name": "RasterizerOrderedTexture1DArray<T>",   "description": [
        "rasterizer-ordered 1D array UAV texture"]},
    {"name": "RasterizerOrderedTexture2D<T>",
        "description": ["rasterizer-ordered 2D UAV texture"]},
    {"name": "RasterizerOrderedTexture2DArray<T>",   "description": [
        "rasterizer-ordered 2D array UAV texture"]},
    {"name": "RasterizerOrderedTexture3D<T>",
        "description": ["rasterizer-ordered 3D UAV texture"]},

    # ------------------------------------------------------------------------
    # GEOMETRY SHADER STREAMS
    # ------------------------------------------------------------------------
    {"name": "PointStream<T>",            "description": [
        "geometry shader output stream of points"]},
    {"name": "LineStream<T>",             "description": [
        "geometry shader output stream of lines"]},
    {"name": "TriangleStream<T>",         "description": [
        "geometry shader output stream of triangles"]},

    # ------------------------------------------------------------------------
    # TESSELLATION PATCH OBJECTS
    # ------------------------------------------------------------------------
    {"name": "InputPatch<T, N>",          "description": [
        "hull shader input control point array"]},
    {"name": "OutputPatch<T, N>",         "description": [
        "domain/hull shader patch control point array"]},

    # ------------------------------------------------------------------------
    # RAYTRACING (DXR)
    # ------------------------------------------------------------------------
    {"name": "RaytracingAccelerationStructure", "description": [
        "top-level acceleration structure SRV resource"]},

    # ------------------------------------------------------------------------
    # SAMPLER FEEDBACK (SM 6.5)
    # ------------------------------------------------------------------------
    {"name": "FeedbackTexture2D<T>",      "description": [
        "sampler feedback-writing texture resource (SM 6.5+)"]},
    {"name": "FeedbackTexture2DArray<T>", "description": [
        "sampler feedback-writing texture array resource (SM 6.5+)"]},

    # ------------------------------------------------------------------------
    # RESOURCE DECLARATION BLOCKS (language-level constructs)
    # ------------------------------------------------------------------------
    {"name": "cbuffer",   "description": [
        "constant buffer declaration block (groups uniform variables)"]},
    {"name": "tbuffer",   "description": [
        "texture buffer declaration block (legacy-style uniform block)"]},

    # ------------------------------------------------------------------------
    # LEGACY (DX9-style HLSL)
    # ------------------------------------------------------------------------
    {"name": "texture",                   "description": [
        "legacy lowercase texture object (deprecated)"]},
    {"name": "sampler",                   "description": [
        "legacy lowercase sampler object (deprecated)"]},
]
