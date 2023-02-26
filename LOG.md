# Log

[中文](https://blog.bujijam.ga/cn/gglu-chat-dev-log/)

## v1.1.1 - 2023/2/26

- **check message**
- **added command**, `/listusers`
- **added invite**, click nick in the sidebar to invite them to a random 8-chars room with sound notification, and add ratelimiter for inviting
- added timestamp for join message

## v1.1.0 - 2023/1/16

- added "do highlight for code"
- **added commands**, `/help`, `/whisper`, `/kick`, `/ban`, `/unban`, `/move`
- added users level, 1-4
- added "fold message", fold message if text length exceeds 750 or the number of lines exceeds 25
- added sidebar, include clear all message, yinjian mode, sound notifications setting, more settings
- **added ratelimiter**, iphash-based
- **added rooms**, create your own room by changing the text after `room?`, join a random room if there is nothing after `room`. e.g. `room?your-room`

## v1.0.1 - 2022/10/23

- added "click nick to @" and sound notification
- added nick storage
- added markdown support

## v1.0.0 - 2022/10/15

- **fixed "multiple join messages after reconnection" bug**
- better looking trip and time display
