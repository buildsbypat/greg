from __future__ import annotations

from gregbot.models.jobs import Job


JOBS: tuple[Job, ...] = (
    Job(
        key="discord_mod",
        name="Discord Mod",
        titles=(
            "Hewwo Kitten",
            "Not now, Daddy is busy",
            "Don't worry Kitten, daddy's here",
        ),
        min_pay=248,
        max_pay=492,
        success_messages=(
            "Greg is surprised you have a job. Pitifully, he gave you {amount}.",
            "You delete a message and called it community management. Greg, while disappointed, gave you {amount}.",
            "You added the rule 'Don't hurt my kitten' to the rules. How did you get {amount} for that?",
            "You muted someone for saying 'first' in general. Greg considered finding a new job while handing you {amount}.",
            "Kitten called you alpha on VC today. Excitedly you got {amount}.",
            "Greg is reconsidering his life choices hiring you. Legally, he had to give you {amount}.",
        ),
        footers=(
            "Greg has never seen power used so... awkwardly.",
            "The mod logs fear you.",
            "You are now emotionally responsible for a channel called 'general'.",
            "Geez, how long since you showered?",
            "**Cleanliness** is next to godliness.",
            "You do know 'kitten' is a 50 year old man, right?",
        ),
    ),
    Job(
        key="it_support",
        name="IT Support",
        titles=(
            "Did you turn it on and off?",
            "Have you logged a ticket for that?",
            "Works on my machine",
        ),
        min_pay=252,
        max_pay=526,
        success_messages=(
            "You fixed the computer by pressing the power button, you earned {amount}.",
            "Turning it off and on worked... surprisingly. Greg gave you {amount}.",
            "You closed a tab on Chrome. You somehow got {amount} for that.",
            "Someone asked you to install Word. You did it and earned {amount}.",
            "'Computer's get vaccines yeah?' The support center gave you {amount} for mental support.",
            "You got asked a question and lied about the answer. Surprisingly you got {amount}.",
        ),
        footers=(
            "The printer remains your enemy.",
            "Greg escalated nothing. It's a miracle.",
            "Client, happy. You, mentally insane.",
            "Chrome tabs currently open: 50",
            "Another ticket done and dusted.",
            "You are a miracle worker you know (just joking).",
        ),
    ),
)