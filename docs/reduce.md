### Continuous surface reduction

Reduction is a tool to keep surfaces from grow without bound. When asked to `reduce <thing>`:

1. Map the surface by studying the thing's code and doc while ignoring other things and the thing's history.
2. Deliniate its responsibility, identify:
   - does it take responsibility it shouldn't?
   - does it not take responsibility it should?
3. Prune error handling and unused endpoints
4. Consolidate and unify the surface
5. Adjust the rest of the project to the new reality
6. Add functions back if they prove highly valuable
