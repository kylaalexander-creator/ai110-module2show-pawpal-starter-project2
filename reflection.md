# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

- What classes did you include, and what responsibilities did you assign to each?

1. Theres needs to be a class for the pet, and a derived class for the owner. there should be a scheduler as parent class, that can add a time, duration, check for time overlap/availability, etc. The derived class can the task, and derived classes of task are the different type of classes. Such as walks, medicine, grooming, feeding. Each responsible for tracking what each task needs, the normal duration for each task etc.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---yes, I fixed the lack of a backlink between the schedule to owner. I let it fix these changes so that there was no issue with tracking tasks according to which owner/pet.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
priority and time. I decided priorty was most important because these are the tasks that typically can not be missed. 
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
 it favors high priority tasks over other tasks, but this can lead to low priority tasks being put off. This is reasonable so the high priority tasks are never put off. 
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Ai to implement the heavy programming, i also used it for brainstorming. Prompts that were most helpful asked for ideas or very clearly asked for specific tasks. broad asks typically needed a lot of redirection.
**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

 I did not accept Ai suggestion as is when deciding what changes to make to the algorithmic logic. Some bottlenecks could occur but fixing them could cause a different error.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
 priority sorting and time conflicts
- Why were these tests important?
these were important because these are the key parts to a well generated schedule. if these didnt work then the schedule would have overlap or certain tasks could be put off.

**b. Confidence**

- How confident are you that your scheduler works correctly?
4 stars.
- What edge cases would you test next if you had more time?

Too many high priority tasks and not enough time. See what occurs to the low priority tasks and how time is managed. 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
 The created the algorithmic logic.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would improve the User interface, it is not what i was expecting when using AI as a tool to help come up with it. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

It is important to be very clear and direct about what you are asking for. Ai takes a lot of freedom is you are not clear enough. It is also good to frequently check what is being implemented both visually in UI and in the code. 