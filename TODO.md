# TODO

## High Priority Features

### Core Functionality

- [x] **Reservations Management**: Add support for managing reservations
  - [x] show
  - [x] add
  - [x] delete
  - [x] update
- [x] **Nodes Management**: Add support for managing nodes
  - [x] show
  - [x] add (?)
  - [x] delete
  - [x] update
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
- [x] **Associations Management**: Add support for managing user-account associations with tree-like display
  - [x] show
  - [x] add
  - [x] delete
  - [x] update
- [x] **Coordinators Management**: Complete coordinator management functionality
  - [x] show
  - [x] create
  - [x] delete
  - [-] update
- [x] **Jobs**
  - [x] show
  - [-] create
  - [x] delete
  - [x] update

### User Interface Improvements

- [x] **Tree-like Associations Display**: Optionally show associations in hierarchical tree format
- [ ] **Interactive Mode**: Add interactive shell mode for better user experience
- [x] **Filter nodes**: Add filter options for nodes by reservation, state, partition, user
- [x] **Filter jobs**: Add jobs options for jobs by reservation, state, partition, user
- [ ] **Selection objects**: Add -L option, which forces to return just list of objects via comma (or -s'separator'),
                             for nodes add -F sub-option for folding in slurm-style.

## Medium Priority Features

- [ ] **drain/undrain**: add commands `drain node-list [[reason=]'reason']`, `undrain/resume`,
      `reboot [asap] [nextstate=...]`, `cancel_reboot ...`;
      use nodelist filters!
- [ ] **hold/top**: add commands `hold {[jobs=]job-list}`, `top ...`,
      `unhold/release ...`, `requeue ...`, `suspend`; use joblist filters!
- [x] **recon[figure], ping, takeover**
- [ ] **token [lifespan=\<lifespan\>] [username=\<username\>]** lifespan=seconds/infinite (we need specify time)
- [x] **version**
- [ ] **batch_script job_id [filename]**
- [ ] **write_config [filename]**
- [ ] **new resources (r/o)** bbstat, burstbuffer, daemons, dwstat, topology
- [ ] **schedloglevel** 0, 1, yes, no, on, off
- [ ] **setdebug** "quiet", "fatal", "error", "info", "verbose", "debug", "debug2", "debug3", "debug4", "debug5" [nodes=...]
- [ ] **setdebugflags** {+|-}\<FLAG\> [{+|-}\<FLAG\>] [nodes=\<NODES\>]
  - Accrue           Accrue counters accounting details
  - Agent            RPC agents (outgoing RPCs from Slurm daemons)
  - AuditRPCs        For all inbound RPCs to slurmctld, print the originating address, authenticated user, and RPC type before the connection is processed.
  - Backfill         Backfill scheduler details
  - BackfillMap      Backfill scheduler to log a very verbose map of reserved resources through time. Combine with Backfill for a verbose and complete view of the backfill scheduler's work.
  - BurstBuffer      Burst Buffer plugin
  - Cgroup           Cgroup details
  - CPU_Bind         CPU binding details for jobs and steps
  - CpuFrequency     Cpu frequency details for jobs and steps using the --cpu-freq option.
  - Data             Generic data structure details.
  - DBD_Agent        RPC agent (outgoing RPCs to the DBD)
  - Dependency       Job dependency debug info
  - Elasticsearch    Elasticsearch debug info (deprecated). Alias of JobComp.
  - Energy           AcctGatherEnergy debug info
  - Federation       Federation scheduling debug info
  - FrontEnd         Front end node details
  - Gres             Generic resource details
  - Hetjob           Heterogeneous job details
  - Gang             Gang scheduling details
  - GLOB_SILENCE     Do not display error message of glob "*" symbols in conf files.
  - JobAccountGather Common job account gathering details (not plugin specific).
  - JobComp          Job Completion plugin details
  - JobContainer     Job container plugin details
  - License          License management details
  - Network          Network details. Warning: activating this flag may cause logging of passwords, tokens or other authentication credentials.
  - NetworkRaw       Dump raw hex values of key Network communications. Warning: This flag will cause very verbose logs and may cause logging of passwords, tokens or other authentication credentials.
  - NodeFeatures     Node Features plugin debug info
  - NO_CONF_HASH     Do not log when the slurm.conf files differ between Slurm daemons
  - Power            Power management plugin and power save (suspend/resume programs) details
  - Priority         Job prioritization
  - Profile          AcctGatherProfile plugins details
  - Protocol         Communication protocol details
  - Reservation      Advanced reservations
  - Route            Message forwarding debug info
  - Script           Debug info regarding any script called by Slurm. This includes slurmctld executed scripts such as PrologSlurmctld and EpilogSlurmctld.
  - SelectType       Resource selection plugin
  - Steps            Slurmctld resource allocation for job steps
  - Switch           Switch plugin
  - TLS              TLS plugin
  - TraceJobs        Trace jobs in slurmctld. It will print detailed job information including state, job ids and allocated nodes counter.
  - Triggers         Slurmctld triggers
  - WorkQueue        Work Queue details

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

