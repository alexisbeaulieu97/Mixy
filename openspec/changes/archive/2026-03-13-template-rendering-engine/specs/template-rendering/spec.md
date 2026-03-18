## ADDED Requirements

### Requirement: Jinja2 content rendering
The TemplateRenderer SHALL render file contents through Jinja2 with the resolved variable context.

#### Scenario: Render simple variable substitution
- **WHEN** a file contains `Hello {{ name }}` and variable `name` resolves to `World`
- **THEN** the rendered content is `Hello World`

#### Scenario: Render with conditionals
- **WHEN** a file contains `{% if use_docker %}Dockerfile{% endif %}` and `use_docker` is `True`
- **THEN** the rendered content includes `Dockerfile`

#### Scenario: Strict undefined variable
- **WHEN** a file references `{{ missing_var }}` and `missing_var` is not in the context
- **THEN** the system raises a rendering error identifying the undefined variable and the file path

### Requirement: Path name rendering
The TemplateRenderer SHALL render file and directory names through Jinja2.

#### Scenario: Render directory name
- **WHEN** a directory is named `{{ project_name }}` and `project_name` is `my_app`
- **THEN** the output directory is named `my_app`

#### Scenario: Render filename
- **WHEN** a file is named `{{ module }}.py` and `module` is `utils`
- **THEN** the output file is named `utils.py`

### Requirement: .j2 suffix stripping
Files ending in `.j2` SHALL always be rendered and the `.j2` suffix SHALL be stripped from the output filename.

#### Scenario: Strip .j2 suffix
- **WHEN** a file is named `Dockerfile.j2`
- **THEN** the output file is named `Dockerfile` and the content is rendered

#### Scenario: Double extension with .j2
- **WHEN** a file is named `config.yaml.j2`
- **THEN** the output file is named `config.yaml` and the content is rendered

### Requirement: Render policy with exclude patterns
The system SHALL render all text files by default and support exclude patterns that force raw copy.

#### Scenario: Exclude pattern skips rendering
- **WHEN** render policy has `exclude: ["*.min.js"]` and file is `app.min.js`
- **THEN** the file is copied without Jinja2 rendering

#### Scenario: Non-excluded text file is rendered
- **WHEN** a `.py` file is not in any exclude pattern
- **THEN** the file is rendered through Jinja2
