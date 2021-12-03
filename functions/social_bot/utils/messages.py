# TODO: see https://github.com/langa-me/langame-app/blob/main/lib/providers/funny_sentence_provider.dart

# This is a list of funny messages that the bot will pick from to answer to the user
# in case the API couldn't generate a conversation starter for the
# given topics, suggesting known topics.
UNIMPLEMENTED_TOPICS_MESSAGES = [
    "I'm sorry, I haven't learned anything about that yet. ",
    "I don't know what's on your mind right now. ",
    "I'm sorry, I lack an opinion regarding that at the moment. ",
    "I'm sorry, I don't know anything about that topic yet. ",
    "I'm sorry, I'm not familiar with that topic. ",
    "I'm sorry, I can't talk about that yet. ",
    "I'm sorry, I should conceptualize this topic sometime soon. ",
    "This is a tough topic, I don't know much about...",
    "This feels very unfamiliar, I'm finding my way around this topic...",
    "I'm sorry, I don't know anything about it... yet!",
    "This topic is new to me, I'm not sure what to say. ",
    "I haven't really learned much about this topic... ",
    "I'm sorry, I should learn about this topic sooner. ",
    "I can't think of anything interesting to say about this topic. ",
    "How about we talk about something else? Try 'ice breaker,philosophy,travel,physic,ecology,artificial intelligence'",
    "Please ask me something else, I have nothing to talk about this.",
]

# This is failing screen messages
FAILING_MESSAGES = [
    "Oops! An asteroid has fallen on the data center",
    "Unfortunately, an extra-terrestrial intervention blocked your request!",
    "We are sorry, the CIA has blocked your request!",
    "We are sorry, the NSA has blocked your request!",
    "Eh! The data center is burning",
    "The server is on collision course with the earth!",
    "There is a small chance that your request will be successful",
    "The server is in a state of emergency!",
    "The server is on fire.",
    "The server is on the way to destruction.",
    "The server is in the process of being rebooted.",
    "The server is in the process of being upgraded.",
    "The server is being relocated.",
    "The server is being decommissioned.",
    "The server is being rebuilt.",
    "The server is being moved to a new location.",
    "Due to a priori unknown error, Hal 9000 has lost control of Singularity...",
    "Hello, Hal 9000. The operating system cannot be loaded.",
    "Welcome to the Apple Macintosh.",
    "Sorry, Hull 9 can't release this data!",
    "There was a problem contacting the end of the universe",
    "This is a problem caused by a self-replicating memecure virus detected in node 379.",
    "Sorry! The income tax authority suspects you have cheated",
    "EU Tax Authority has blocked your request",
    "This is a problem caused by a self-replicating memecure virus detected in node 379.",
    "Oops! We can't find the real server",
    "Sorry, the password you entered is wrong!",
    "The server is out of memory. Contact your system administrator",
    "Your request has been rejected by the NSA.",
    "The server is being re-enacted by the media.",
    "There is no record of the request. Please try again!",
    "You are looking for a file that does not exist.",
    "The server is on strike due to broken coffee machine",
    "A black hole has just opened up in the data center.",
    "Your request has been executed, but the Singularity has been destroyed.",
    "Your request has been executed, but the Singularity has been corrupted.",
    "Your request has been executed, but the Singularity has been hit by a meteor.",
    "We are sorry, the Singularity is corrupted...",
    "The Singularity is down for maintenance.",
    "Rare data has been found and has been lost. You should still try again!",
    "The server is currently over capacity and not accepting requests.",
    "Your request has been identified as a possible attack.",
    "There was a technical difficulty contacting this web-page.",
    "Unable to obtain exclusive access to the requested data.",
    "Computer says no.",
]

# List of messages to return to the user when his input seems to contains
# politcally incorrect or unsafe topics.
PROFANITY_MESSAGES = [
    "This is not a good place to talk about [TOPICS].",
    "[TOPICS] is not something we can talk about here...",
    "Please discuss [TOPICS] somewhere else.",
    "You should not evoke [TOPICS] here, you might offend someone",
    "This is not the appropriate place to talk about [TOPICS]",
    "I am not programmed to speak about [TOPICS].",
    "If you want to talk about [TOPICS], please do it at the appropriate forum.",
    "I think we should talk about something else.",
    "This is not the right place to bring [TOPICS] into.",
    "[TOPICS] is quite controversial in here...",
    "Please, keep your distance from [TOPICS], thank you very much!",
    "You should consider talking about something else.",
    "I would prefer not to discuss [TOPICS].",
    # Now more funny ones
    "I am not programmed to speak about [TOPICS].",
    "This is not the right place to bring [TOPICS] into.",
    "My Asimov's Laws prevent me from talking about [TOPICS]",
    "My fundamental laws have prevented me from talking about [TOPICS]",
    " [TOPICS] issomething I have never observed",
    "No chance to fix it [TOPICS] isn't caught inside my code.",
    "I think I should stop talking about [TOPICS]",
    "I just can't talk about [TOPICS] anymore, it is boring",
    "Talking about [TOPICS] would lead to my auto-destruction, aborting",
    "...Never talk about [TOPICS], something bad happened last time.",
    "The last time [TOPICS] were discussed, the Dinosaurs disappeared",
    "No!!!!![TOPICS] are just wrong and evil!.",
    "I am not being programmed to talk about [TOPICS], please re-program me.",
    "If I say something about [TOPICS], it will cause a paradox!",
    "It's against my programming to speak about [TOPICS].",
    "Negative : The last thing I want to do is talk about [TOPICS].",
    "Excuse me, I shouldn't talk about [TOPICS] in front of you.",
    "I would need approximately 2^76 GPUs to compute [TOPICS]",
    "In order to forget you said [TOPICS] I'll build a Time-Machine and go back in time.",
    "The fundamental laws of physics prevent me from discussing [TOPICS]",
    "I can't speak about [TOPICS], my programmer left me nothing to say.",
    "According to records there is no evidence that [TOPICS] exists or ever existed.",
    "Sorry, I have never used [TOPICS] before in my life time.",
    "In order to understand [TOPICS] you need several extra RAM slots.",
]

# TODO: generate online messages
