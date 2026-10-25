# Personas and user stories

The spec that entity design, `/grill-me` sessions and `/code-review` (Spec
axis) check against.

## Familjen Lind: staffed and Meröppet in one household

Two parents and two school-age kids in Linköping, with a grandparent who
often joins them.

- One parent has a library card with a PIN for **Meröppet** (self-service
  access). They drop in on evenings and weekends to collect reservations and
  return books, and don't need staff.
- The kids go after school, when the library is **staffed**: they get help
  from the librarian, story hour, and homework help.
- The grandparent needs **staffed** hours for help with the self-checkout.
- The family uses one Home Assistant dashboard on the kitchen tablet and
  follows two libraries: the main library in town and the small local branch.

So, for the same library on the same day, the household needs both answers:
*is someone working there now?* and *can we get in with the card now?* Neither
answer is a setting; both matter every day.

### User story

> As a family that uses both staffed and Meröppet hours, I want to see for
> each of our libraries whether it is staffed now and whether we can get in
> with our card now, together with today's hours for each, so that we can
> decide whether to bring the kids for help or just pop in, without having to
> choose one mode when setting up the integration.

### Acceptance criteria

1. Setup only asks which libraries to follow; there is no staffed vs.
   self-service choice.
2. Each library is its own device with three entities: today's hours,
   **Bemannat** (staffed) open/closed, and **Meröppet** (cardholder can get
   in: staffed *or* self-service hours) open/closed.
3. **Consistency:** each open/closed entity is on exactly when the current
   time falls inside the hours it shows in its own `hours` attribute. The
   door state and the listed hours never disagree.
4. A closed day reads as `Stängt` everywhere.
5. Removing a library from the favorites (Configure) removes its device.
