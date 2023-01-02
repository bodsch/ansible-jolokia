
# Ansible Role:  `jolokia`

Ansible role to install an jolokia application into an tomcat

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-jolokia/main.yml?branch=main)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-jolokia)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-jolokia)][releases]
[![Ansible Quality Score](https://img.shields.io/ansible/quality/50067?label=role%20quality)][quality]

[ci]: https://github.com/bodsch/ansible-jolokia/actions
[issues]: https://github.com/bodsch/ansible-jolokia/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-jolokia/releases
[quality]: https://galaxy.ansible.com/bodsch/jolokia


## Requirements & Dependencies

- java
- python3
- apache tomcat 9

### Operating systems

Tested on

* Debian based
    - Debian 10 / 11
    - Ubuntu 20.04

## usage


```yaml
jolokia_version: 1.6.2
jolokia_file_name: "jolokia-war-{{ jolokia_version }}.war"
jolokia_download_url: "https://repo1.maven.org/maven2/org/jolokia/jolokia-war/{{ jolokia_version }}/{{ jolokia_file_name }}"

jolokia_home: /opt/jolokia

jolokia_user: jolokia
jolokia_group: jolokia

jolokia_debug: false

jolokia_systemd:
  restart: 'on-failure'
  restart_sleep: '20s'

jolokia_tomcat: {}

jolokia_jmx_remote:
  port: 22222
  authenticate: 'false'
  ssl: 'false'
```

To configure tomcat: (for [example](vars/main.yml))

```yaml
jolokia_tomcat:
  roles: []
  users: []
```

For example, add a user and a role for security reason:

```yaml
jolokia_tomcat:
  roles:
    - jolokia
  users:
    - username: monitoring
      password: monitoring
      roles:
        - jolokia
```

Tweak tomcat memory settings:

```yaml
jolokia_tomcat:
  initial_heap_size: 64m
  max_heap_size: 256m
```


To configure own Catalina options. ([defaults](defaults/main.yml))

```yaml
jolokia_catalina_opts: []
```


To enable and configure optional logrotate. ([defaults](defaults/main.yml))

```yaml
jolokia_logrotate: {}
```



## Author

- Bodo Schulz

## License

[Apache](LICENSE)

`FREE SOFTWARE, HELL YEAH!`
