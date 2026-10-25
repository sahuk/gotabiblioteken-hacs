# Personas and user stories

The spec that entity design, `/grill-me` sessions and `/code-review` (Spec
axis) check against.

## Default: "can I get in?"

Most people with a library card don't care whether staff are on duty. Meröppet
(self-service access with card + PIN) is a normal way in, so for them the
library is **open** whenever they can enter, staffed or not. That is the
default answer the integration gives.

## Familjen Lind: also needs to know when staff are there

Two parents and two school-age kids in Linköping, with a grandparent who
often joins them.

- The parents use the library like most people: they drop in with the card
  on evenings and weekends to collect reservations, staffed or Meröppet. They
  only need **Open** (Öppet).
- The kids and the grandparent need **in-person support**: the kids come for
  homework help and story hour, and the grandparent needs help with the
  self-checkout. For them the library is only useful when it is **staffed**.
- The family uses one Home Assistant dashboard on the kitchen tablet and
  follows two libraries: the main library in town and the small local branch.

So staffed-only is the exception, needed by people who rely on in-person help
(kids, the elderly), not a different mode of the integration.

### User story

> As a family where the adults just need to know when they can get in, but
> the kids and grandparents need staff on site, I want each library to show
> whether it is open now and, if we turn it on, whether it is staffed now,
> together with today's hours for each, so that everyone can tell at a glance
> whether a trip to the library works for them, without choosing one mode
> when setting up the integration.

### Acceptance criteria

1. Setup only asks which libraries to follow; there is no staffed vs.
   self-service choice.
2. Each library is its own device with today's hours and an **Open** (Öppet)
   open/closed sensor (open during staffed *or* Meröppet hours).
3. Each library also gets a **Staffed** (Bemannat, Yes/No) sensor, created
   **disabled**. Those who need in-person support enable it per library.
   It never shows "closed" while the library is open for Meröppet.
4. **Consistency:** each open/closed entity is on exactly when the current
   time falls inside the hours it shows in its own `hours` attribute. The
   state and the listed hours never disagree.
5. A closed day reads as closed everywhere (`Closed`, or `Stängt` in Swedish).
6. Removing a library from the favorites (Configure) removes its device.
7. Names and generated text follow Home Assistant's language: Swedish for a
   Swedish setup, English for every other language. Nothing user-facing is
   hard-coded Swedish.
8. Names lead with what tells libraries apart: the place ("Motala Open",
   "Agora Opening hours"), not a shared word like "bibliotek", so a name cut
   off on a dashboard card still identifies the library.
