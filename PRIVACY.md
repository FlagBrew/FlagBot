# FlagBot Privacy Policy

Last updated: 2026-10-07

FlagBot is the moderation and utility bot for the [FlagBrew Discord server](https://discord.gg/bGKEyfY). The FlagBrew team runs it. It operates only in the FlagBrew server and a private testing server, and it leaves any other server it is added to.

This policy explains what FlagBot reads, what it stores, and what it shares. Discord's own [Privacy Policy](https://discord.com/privacy) covers everything Discord itself does with your data.

## What FlagBot reads

FlagBot reads the following data through Discord while it runs. It does not keep this data outside Discord unless the next section says so.

| Data | Why |
| --- | --- |
| Messages in the FlagBrew server | To run commands, and to log edited and deleted messages for moderators |
| Attachments sent with commands | To accept crash dump submissions and moderator evidence for warns and bans |
| Member joins, leaves, nickname changes and timeouts | To log them for moderators and re-apply mutes to members who rejoin |
| Online status and activity | Only when someone runs the `userinfo` command. The result is shown in that channel and never stored |
| Direct messages sent to FlagBot | To forward them, with attachments, to moderators |

## Staff logs

FlagBot posts the following to private channels on the FlagBrew server that only moderators and the FlagBrew team can see:

- member joins and leaves, including account age
- nickname changes and timeouts
- the original and edited text of edited messages, and the text of deleted messages
- direct messages sent to FlagBot
- submitted crash dumps and their descriptions
- thread creation, archiving and deletion

These logs stay on Discord until staff delete them.

## What FlagBot stores outside Discord

FlagBot keeps the following records in files on the machine that hosts it. Warnings can also be copied to a MongoDB database run by the FlagBrew team.

| Record | Contents | Kept until |
| --- | --- | --- |
| Warnings | Your user ID, the warning reason, the date, and the moderator's username | A moderator deletes or clears the warning |
| Mutes | Your user ID and the time your mute expires | The expiry time is cleared when the mute ends, but your user ID stays in the file |
| FAQ by DM | Your user ID, if you turned on FAQ answers by DM | You run `toggledmfaq` again |
| Crash dump hashes | A SHA-1 hash of each submitted crash dump file, used to reject duplicates | Staff clear the hash list |

FlagBot does not store message content outside Discord, except for the warning reasons that moderators type into the `warn` command.

## What FlagBot shares

- The `report_code` command opens a public issue on the [FlagBrew/Sharkive](https://github.com/FlagBrew/Sharkive) GitHub repository. The issue includes your Discord username, your user ID and the text of your report.
- FlagBot does not sell your data or share it with advertisers.
- FlagBot does not use your data to train machine learning or AI models.

## Your choices

- Run `toggledmfaq` to add or remove yourself from the FAQ by DM list.
- If you leave the FlagBrew server, FlagBot stops reading your messages and member events. Records it already stored remain until removed.
- To ask what FlagBot stores about you, or to ask for it to be deleted, email `flagbrewinfo@gmail.com`. Moderation records may be kept where they are needed to enforce the server rules.

## Changes

Changes to this policy are made in this file. The repository's commit history shows every past version.

## Contact

Email `flagbrewinfo@gmail.com` with any questions about this policy.
