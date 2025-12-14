## Project Features

HLSL language server will provide following features:

- Code Validation & Errors
- Code Completion / Autosuggestion
- Goto Definition
- Hover to see documentation
- Code formatting
- Refactoring (Renaming)
- Preprocessor support for all above features
- In place macro expansion

## Suggested features

- Warnings and Suggestions based on performance and branching of the program, providing branchless/optimised code when possible.
- Further refactoring (extract to method definition, extract expression to variable).

## Project Tasks
- Client-server communication (done)
- Language Parser (wip)
- Editor workspace management
- Syntax features

## Editor Integration

Install the language server in your $PATH.

### Kakoune (using [kakoune-lsp](https://github.com/kakoune-lsp/kakoune-lsp))
In the lsp configuration file, add

```
hook -group lsp-filetype-hlsl global BufSetOption filetype=hlsl %{
    set-option buffer lsp_servers %{
        [hlsl-language-server]
        root_globs = [ "*.hlsl", "*.fx" ]
        command = "hlslls"
    }
}
```

