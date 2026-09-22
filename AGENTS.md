# Release workflow

- Develop future visual and interaction changes in the local staging/review routes first.
- Show Brian the staging version and wait for explicit approval before promoting changes to the main experience or deploying production.
- An implementation request alone is not permission to publish brianbzeng.com.
- On 2026-09-11, Brian approved the latest shelf-motion staging (v158 return timing) and requested promotion of the current room site to brianbzeng.com.
- On 2026-09-21, Brian requested the "New!" room-menu redirect into the monitor and Notes-over-terminal greeting; the Manic lettering primitive is approved for that note only. Implemented locally, not yet deployed.
- Preserve the existing production host/domain. Never substitute a separate demo deployment for the requested domain.
- Keep local Blender authoring files and raw render outputs out of deployment artifacts; retain the runtime assets required by the approved site.
- Use bounded parallel subagents for independent useful work, with non-overlapping ownership. Coordinate Blender, native-app control, and heavy rendering.
