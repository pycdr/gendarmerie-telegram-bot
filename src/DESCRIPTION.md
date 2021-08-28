# BHM model

this model gets/sends all messages, queries, medias, ... by `Bot` part. it uses `Handler` part to check and handle messages and database. then, `Model` helps this part to connect with database.

```text
.___________.         ._____________.
|           | ------- |             |
|   Moedl   | <------ |   Handler   |
|___________|         |_____________|
                         ^  |
                         |  |
                         |  |
                         |  v
.__________.          ._________.
|          | <------- |         |
|   User   |          |   Bot   |
|__________| -------> |_________|
```
