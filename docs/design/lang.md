# Language Design

Generics are not a great solution to prevent code duplication. I can also use:
* subclassing

Subclassing
* Define a parent expr class. Child classes can override the set of valid functions that can be called. It won't be as type safe as using enums, but it's at least *somewhat* typesafe.
