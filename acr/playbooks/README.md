# Playbooks

A playbook is a YAML file with a list of rules. Each rule checks the signals
acr found and, if everything matches, adds one outreach angle to the brief.
No Python needed. Add a .yml file to this folder and run acr.

## Rule format

    name: My playbook
    rules:
      - id: unique-rule-id
        when:
          lacks_category: [chat]
          has_page: [pricing]
        angle: "Text shown in the brief. You can use {domain}, {ats}, {stack}."
        verify: true
        priority: 5

All conditions in `when` must match (AND). An empty `when` always matches.

## Conditions

- has_tech / has_all_tech / lacks_tech: technology names, as listed in acr/data/tech.yml
- has_category / lacks_category: tech categories (crm, chat, analytics, tag-manager, advertising, payments, ecommerce, cms, framework, scheduling, forms, cdn)
- has_page / lacks_page: about, careers, jobs, pricing, blog, customers
- hiring_platform: true or false (an applicant tracking system was found)
- github_min_repos: minimum number of public repos
- github_language: any of these in the org's top languages
- text_contains: any keyword in the title, description or headline

## Options

- verify: true appends a "verify first" note, for rules based on something missing
- priority: higher numbers appear first (default 0)

## Check your rules

    acr --check-playbooks
    acr --check-playbooks --playbooks path/to/my-rules.yml

## Share yours

Open a pull request with a new file, such as fintech.yml.
Include one real domain where your rule fires.
