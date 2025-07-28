from adaptivecards.template import Template

USER_TEMPLATE = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "type": "AdaptiveCard",
    "body": [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "altText": "",
                            "url": "${imageUri}",
                            "style": "Person",
                            "size": "Small",
                        }
                    ],
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "TextBlock",
                            "weight": "Bolder",
                            "text": "${displayName}",
                        },
                        {
                            "type": "Container",
                            "spacing": "Small",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "${toUpper(jobTitle)}",
                                    "spacing": "Small",
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "${mail}",
                                    "spacing": "None",
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "${givenName}",
                                    "spacing": "None",
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "${surname}",
                                    "spacing": "None",
                                },
                            ],
                        },
                    ],
                },
            ],
        }
    ],
}

PR_TEMPLATE = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.4",
    "body": [
        {"type": "TextBlock", "text": "${title}", "weight": "Bolder", "size": "Medium"},
        {"type": "TextBlock", "text": "${url}"},
    ],
    "actions": [
        {"type": "Action.OpenUrl", "title": "View Pull Request", "url": "${url}"}
    ],
}


def create_profile_card(profile):
    template = Template(USER_TEMPLATE)
    return template.expand(profile)


def create_pr_card(pr):
    template = Template(PR_TEMPLATE)
    return template.expand(
        {"$root": {"title": pr.title, "url": pr.html_url, "id": pr.id}}
    )
