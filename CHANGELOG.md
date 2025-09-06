# Changelog

All notable changes to the Kaggle Discussion Extractor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added
- Initial release of Kaggle Discussion Extractor
- Full hierarchical reply extraction with proper parent-child relationships
- Automatic pagination support for extracting all discussions from a competition
- Clean content extraction without duplication between parent and nested replies
- Author metadata extraction including:
  - Competition rankings ("Nth in this Competition")
  - User badges (Competition Host, Expert, Master, Grandmaster)
  - Profile URLs
- Engagement metrics (upvotes/downvotes) for all posts and replies
- Multiple output formats (JSON and Markdown)
- Command-line interface with various options
- Async/await architecture for better performance
- Configurable rate limiting and delays
- Comprehensive logging system
- Type hints throughout the codebase
- Full test suite with pytest
- GitHub Actions CI/CD pipeline
- Professional documentation and examples

### Features
- Extract single discussions or entire competitions
- Hierarchical numbering system (1, 1.1, 1.2, etc.)
- Clean markdown output for easy reading
- JSON export for programmatic processing
- Statistics generation for discussions
- Batch processing capabilities
- Error recovery and robust handling
- Headless and GUI browser modes
- Customizable configuration

### Technical Details
- Built with Playwright for reliable web automation
- Async/await pattern for efficient processing
- Clean architecture with separation of concerns
- Full type annotations for better IDE support
- Comprehensive error handling
- Modular design for easy extension

## [Unreleased]

### Planned Features
- Support for dataset and notebook discussions
- Discussion search and filtering capabilities
- CSV export format
- Web dashboard for visualization
- Sentiment analysis for discussions
- Caching system for faster re-extraction
- Real-time monitoring for new discussions
- GraphQL API support
- Bulk export utilities
- Integration with Kaggle API

### Known Issues
- Rate limiting may occur with very large competitions
- Some special characters in titles may cause filename issues on Windows
- Deeply nested replies (>3 levels) may not be fully captured in some cases

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

## Support

For questions, bug reports, or feature requests, please [open an issue](https://github.com/yourusername/kaggle-discussion-extractor/issues) on GitHub.