# TODO

## High Priority Features

### Core Functionality

- [x] **Reservations Management**: Add support for managing reservations
  - [x] show
  - [x] add
  - [x] delete
  - [x] update
- [ ] **Nodes Management**: Add support for managing nodes
  - [ ] show
  - [ ] add
  - [ ] delete
  - [ ] update
- [x] **QOS Management**: Add support for managing qos
  - [x] show
  - [x] create (with autocomplete for QOS_OPTIONS, QOS_FLAGS, PREEMPT_MODE_VALUES)
  - [x] delete
  - [x] update
- [x] **Partition Management**: Add support for managing partitions
  - [x] show
  - [x] create
  - [x] delete
  - [x] update
- [x] **Accounts Management**: Add support for managing accounts
  - [x] show (with filter support: `organization=nvidia`)
  - [x] create (with autocomplete for ACCOUNT_OPTIONS)
  - [x] delete
  - [x] update (simple mode and WHERE/SET bulk mode)
- [x] **Users Management**: Add support for managing users
  - [x] show
  - [x] create
  - [x] delete
  - [x] update
- [ ] **Associations Management**: Add support for managing user-account associations with tree-like display
  - [x] show
  - [x] add
  - [ ] delete
  - [ ] update
- [ ] **Coordinators Management**: Complete coordinator management functionality
  - [x] show
  - [x] create
  - [ ] delete
  - [ ] update

### User Interface Improvements

- [ ] **Tree-like Associations Display**: Optionally show associations in hierarchical tree format
- [ ] **Enhanced Output Formats**: Add more output format options (CSV, YAML, XML)
- [ ] **Interactive Mode**: Add interactive shell mode for better user experience
- [ ] **Progress Indicators**: Add progress bars for long-running operations

## Medium Priority Features

### Additional Functionality

- [ ] **Interactive Table Editor**: Add urw-scroll-table to show/edit accounts, partitions, nodes, etc

### Documentation & Help

- [ ] **Complete Documentation**: Create comprehensive Sphinx documentation
- [ ] **API Documentation**: Add detailed API documentation for all commands
- [ ] **Examples & Tutorials**: Add usage examples and tutorials
- [ ] **Man Pages**: Generate man pages for the CLI tool
- [ ] **Video Tutorials**: Create video demonstrations of key features

### Configuration & Customization

- [ ] **Configuration File**: Add support for configuration files (~/.slurm-cli/config)
- [ ] **Theme Support**: Add customizable themes and color schemes
- [ ] **Custom Aliases**: Allow users to define custom command aliases
- [ ] **Plugin System**: Add plugin architecture for extending functionality

### Performance & Reliability

- [ ] **Caching Improvements**: Optimize caching mechanism and eliminate double checking
- [ ] **Error Handling**: Improve error handling and user-friendly error messages
- [ ] **Validation**: Add comprehensive input validation for all commands
- [ ] **Retry Logic**: Add retry logic for network operations

## Low Priority Features

### Advanced Features

- [ ] **Job Management**: Implement comprehensive job management features (show, update, cancel jobs)
- [x] **JSON**: Add json output format (--json or --style json)
- [ ] **Backup/Restore**: Add slurm config backup and restore capabilities

### Integration & Compatibility

- [ ] **Slurm REST API Integration**: Integrate with Slurm REST API

### Development & Testing

- [ ] **Integration Tests**: Add comprehensive integration tests
- [ ] **Performance Tests**: Add performance benchmarking
- [ ] **Load Testing**: Add load testing for high-traffic scenarios
- [ ] **Docker Support**: Add Docker containerization
- [ ] **CI/CD Pipeline**: Complete GitHub Actions CI/CD pipeline

## Code Quality & Maintenance

### Code Improvements

- [ ] **Type Hints**: Complete type hints for all functions
- [ ] **Code Coverage**: Achieve 90%+ test coverage
- [ ] **Refactoring**: Refactor large functions and classes
- [ ] **Documentation**: Add comprehensive docstrings
- [ ] **Code Comments**: Add inline comments for complex logic

### Dependencies & Security

- [ ] **Dependency Updates**: Keep dependencies up to date
- [ ] **Security Audit**: Perform security audit of dependencies
- [ ] **Vulnerability Scanning**: Add automated vulnerability scanning
- [ ] **License Compliance**: Ensure license compliance

## Known Issues & Bugs

### Current Issues

- [ ] **Double Cache Checking**: Eliminate double checking of cached resources (line 505 in cli.py)
- [ ] **Validation TODO**: Check if values are valid QoS, partition, etc. (line 90 in base_resource.py)
- [ ] **Error Messages**: Improve error messages for better user experience
- [ ] **Edge Cases**: Handle edge cases in resource management

## Future Considerations

### Long-term Goals

- [ ] **Multi-cluster Support**: Support for managing multiple Slurm clusters
- [ ] **Federation Support**: Add support for Slurm federation
- [ ] **Cloud Integration**: Add cloud provider integrations
- [ ] **Monitoring Integration**: Integrate with monitoring systems (Prometheus, Grafana)
- [ ] **Alerting**: Add alerting capabilities for cluster issues

### Research & Innovation

- [ ] **Machine Learning**: Add ML-based resource optimization suggestions
- [ ] **Predictive Analytics**: Add predictive analytics for resource usage
- [ ] **Auto-scaling**: Add auto-scaling capabilities
- [ ] **Cost Optimization**: Add cost optimization features

## Notes

- Priority levels are based on user impact and implementation complexity
- Items marked with [ ] are not started, [x] are completed
- Consider breaking down large items into smaller, manageable tasks
- Regular review and updates of this TODO list are recommended
