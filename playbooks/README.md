# Playbooks

A playbook is a YAML file with a list of rules. Each rule checks the signals
acr.py found and, if everything matches, adds one outreach angle to the brief.
No Python needed. Drop a .yml file in this folder and run acr.py.

## Rule format

    name: My playbook
    rules:
      - id: unique-rule-id
        when:
          lacks_tech: [Intercom, Drift]
          has_page: [pricing]
        angle: "Text shown in the brief. You can use {domain}, {ats}, {stack}."
        verify: true
        priority: 5

All conditions in `when` must match (AND). An empty `when` always matches.

## Conditions

- has_tech: any of these technologies detected
- has_all_tech: all of these detected
- lacks_tech: none of these detected
- has_page: any of these pages exist (about, careers, jobs, pricing, blog, customers)
- lacks_page: none of these pages exist
- hiring_platform: true or false (an ATS like Greenhouse or Lever was found)
- github_min_repos: number, minimum public repos
- github_language: any of these in the org's top languages
- text_contains: any keyword in the title, description or headline

## Options

- verify: true appends a "verify first" note, for rules based on something missing
- priority: higher numbers appear first (default 0)

## Check your rules

    python acr.py --check-playbooks

## Share yours

Open a pull request with a new file, such as playbooks/fintech.yml.
Include one real domain where your rule fires.
