# MCP (Mod Control Panel) Server with GitHub Integration

A comprehensive MCP server application with GitHub integration, providing tools for repository management, version control, and code search functionality.

## Features

### GitHub Integration
- OAuth 2.0 authentication for GitHub API access
- Repository metadata retrieval (repos, branches, commits, contributors)
- File content and history access
- Commit comparison functionality

### Version Control
- Git repository cloning and management
- Branch creation, checkout, and management
- Local and remote branch synchronization
- Commit and push operations
- Repository status monitoring

### Code Search
- Keyword search with case sensitivity options
- Code snippet matching
- Regular expression support
- File type filtering
- File structure visualization

### Security Features
- OAuth 2.0 resource server functionality
- JWT token validation
- Path traversal protection
- Rate limiting for API requests
- Operation logging and audit trails
- Input validation and sanitization

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
app/
├── main.py          # MCP server entry point and tool/resource definitions
├── config.py        # Pydantic settings management
├── github_api.py    # GitHub API interaction with PyGitHub
├── vcs.py           # Local Git repository operations with GitPython
├── code_search.py   # Code search functionality
├── auth.py          # Authentication and authorization utilities
└── utils.py         # Common utilities (caching, rate limiting, etc.)
```

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- GitHub personal access token (for GitHub API access)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/gsmcp.git
   cd gsmcp
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:

   Create a `.env` file in the project root with the following content:

   ```env
   # Server configuration
   HOST=0.0.0.0
   PORT=8000
   LOG_LEVEL=INFO
   
   # GitHub configuration
   GITHUB_TOKEN=your_github_token_here
   GITHUB_API_URL=https://api.github.com
   
   # Local repository settings
   LOCAL_REPO_DIR=./repos
   
   # JWT configuration
   JWT_SECRET_KEY=your_jwt_secret_key_here
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

### Running the Server

```bash
python -m app.main
```

The server will start on `http://localhost:8000` by default, using the streamable HTTP transport.

## Usage

### MCP Tools

The server exposes the following tools:

#### GitHub Tools
- `get_github_repos`: List repositories for a GitHub user/organization
- `get_github_repo_info`: Get detailed information about a repository
- `get_github_branches`: List branches in a repository
- `get_github_commits`: Get commit history for a branch
- `get_github_contributors`: List repository contributors
- `get_github_file_content`: Get content of a file in a repository
- `get_github_file_history`: Get history of a file
- `compare_github_commits`: Compare two commits

#### Version Control Tools
- `clone_repository`: Clone a remote repository to local
- `checkout_branch`: Switch or create a branch
- `commit_changes`: Commit local changes
- `push_changes`: Push changes to remote repository
- `get_local_branches`: List local branches
- `get_remote_branches`: List remote branches
- `get_repo_status`: Get repository status

#### Code Search Tools
- `search_code`: Search for keywords in a repository
- `search_code_snippet`: Search for code snippets
- `search_by_regex`: Search using regular expressions
- `get_repo_file_structure`: Get repository file structure

### MCP Resources

- `github://repos/{owner}`: Get repository list for a GitHub user/organization
- `github://repo/{owner}/{repo}`: Get detailed repository information
- `github://file/{owner}/{repo}/{path}`: Get file content from a repository

## Security Considerations

1. **Token Security**: Always keep your GitHub token and JWT secret key secure. Never commit them to version control.

2. **Rate Limiting**: The server implements rate limiting to prevent abuse. Adjust the `RATE_LIMIT_CAPACITY` and `RATE_LIMIT_REFILL_RATE` in `config.py` as needed.

3. **Path Validation**: The server validates all file paths to prevent path traversal attacks.

4. **Operation Logging**: All critical operations are logged with user information for audit purposes.

5. **Input Sanitization**: All user inputs are sanitized to prevent injection attacks.

## Configuration

The application uses Pydantic settings management with support for environment variables. Configuration options are defined in `app/config.py`:

- `HOST`: Server host address
- `PORT`: Server port
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `GITHUB_TOKEN`: GitHub personal access token
- `GITHUB_API_URL`: GitHub API base URL
- `LOCAL_REPO_DIR`: Directory for storing local repositories
- `JWT_SECRET_KEY`: Secret key for JWT token validation
- `JWT_ALGORITHM`: Algorithm used for JWT tokens
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration time

## Testing

Run the test suite using pytest:

```bash
python -m pytest
```

The test suite includes tests for:
- GitHub API interaction
- Version control operations
- Utility functions
- Security mechanisms

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for your changes
5. Run the test suite to ensure all tests pass
6. Submit a pull request

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - The protocol used for server-client communication
- [PyGitHub](https://pygithub.readthedocs.io/) - GitHub API client for Python
- [GitPython](https://gitpython.readthedocs.io/) - Git wrapper for Python
- [FastMCP](https://modelcontextprotocol.io/sdk/python) - MCP server implementation
- [Pydantic](https://pydantic.dev/) - Data validation and settings management
- [Python-jose](https://python-jose.readthedocs.io/) - JWT implementation for Python

## Support

For issues, questions, or feature requests, please open an issue on the [GitHub repository](https://github.com/your-username/gsmcp/issues).
