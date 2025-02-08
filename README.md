# hornsync

### Basic idea proposal: 
Some sort of web application that consolidates club / org information and events via google calendar. A club can register and add a bunch of information about their club, including categories (e.g. academic, social, fitness, etc.). And the main thing - they add their google calendar url, which already automatically syncs events to anyone who has their calendar saved. Then, any student who registers for an account (this registration process should be distinct from the club one) can choose clubs from a dropdown that they want to follow, and click some generate button, and then all events across all the clubs they have selected will be added to a new google calendar that they can subscribe to. 

Ideally it would be nice if the app could offer suggestions for the student based on their selected interests / categories, but not sure if I will have time for that.

#### Logistics and tech stack
I'm no SWE or mobile app developer so I might stick w streamlit for my UI with hopes that the idea and execution is more heavily favored.
* Python
* Streamlit
* Google Calendar API
* Firebase or SQLite for user authentication and DB storage