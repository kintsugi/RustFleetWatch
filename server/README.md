# Rust Fleet Watchlist Server Docs

##Models

###Users

Users will not use the typical username/pw auth scheme. When a user first connects through their web browser, a user instance is created for them and they are issued a user ID and an non-expiry access token that should be stored in their cookies. Users that do not already have it in their cookies are assumed to be new users.

####Relations

* A User has many Rooms `name: ownedRooms`
* A User has many Squads `name: ownedSquads`
* A User has many Squad Connections `name: joinedSquads`

####Attributes

* `socketId: String` socketIO socket id of the user

###Rooms

A room is a collection of squads. There is a short(6-8 characters) string that acts as the rooms url i.e. (url.com/xxxxxxxx)

####Attributes

* `link: String` url identifier for the room
* `joinLink: String` Link given to room owner to distribute to friends to join with client
* `leaderLink: String` Link given to room owner to use themselves to join with client

####Relations
* A Room has many Squads
* A Room belongs to a User `name: commander, fk: commanderId`

###Squads

A collection of squad members and a squad name

####Relations

* A Squad has many Users through a Squad Connection `name: members`
* A Squad belongs to a User `name: leader, fk: leaderId`
* A Squad belongs to a Room

####Attributes

* `name: String` name of the room

###Squad Connections

Through model between a User and a Squad

####Relations
* A Squad Connection belongs to a User
* A Squad Connection belongs to a Squad
