# Phase 1.8.2 qualification workflow race

On the initial 1.8.2 merge, the long-window workflow and adaptive qualification workflow were triggered concurrently. The long-window job could therefore read the prior operational adaptive artifact before the new 1.8.2 run completed. This produced a wrapper labeled `critical-reserve-v1` around an older adaptive payload.

This artifact is not accepted as valid 1.8.2 longitudinal evidence. The archiver is being hardened to require the nested adaptive payload's `qualification_epoch` to match the target epoch, and automatic long-window execution on code pushes is removed. Scheduled/manual long-window runs occur only after an adaptive qualification artifact exists.
