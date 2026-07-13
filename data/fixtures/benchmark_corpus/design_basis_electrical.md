# Electrical Design Basis — Reference Notes

Synthesized reference notes covering general electrical engineering
principles used across the project. See `README.md` for provenance.

## Grounding Philosophy

The facility uses a single point of grounding (star grounding) for all
major equipment: lower electrical noise, better EMI control, but a
single-point failure risk at the star point. Multiple ground paths give
better fault tolerance but introduce higher loop inductance and potential
ground loops. Tier III facilities typically specify star grounding with
redundant ground paths to the star point.

## Neutral Grounding Resistor (NGR) Fault Current

The project's neutral grounding resistor is rated 6.25 Ohms on a 3-phase
415V system. For a line-to-ground fault, fault current is approximately
415V / 6.25Ω ≈ 66A. This is a moderate fault current for a 415V industrial
system and should be cleared in under 1 second by coordinated protective
relays to prevent transformer heating.

## Harmonic Distortion from Variable Frequency Drives

Variable frequency drive (VFD) motors generate 5th, 7th, 11th, and 13th
harmonic currents. Sensitive IT equipment (servers, storage) is vulnerable
to harmonic distortion above roughly 5% total harmonic distortion (THD).
Where VFDs share a switchboard with sensitive IT loads, mitigation is line
reactors on VFD inputs and/or active harmonic filters on the switchboard.

## Transient Overvoltage Protection

When a large inductive load (such as a chiller compressor motor) is
switched off by a contactor, the collapsing magnetic field can produce a
voltage transient that damages downstream equipment. Standard protection
is surge protection devices (SPDs / varistors) or RC snubber circuits
across the contactor coil or load; their absence on a single-line diagram
indicates a design gap that can cause nuisance equipment failures.

## Utility / Generator Synchronization and ATS Logic

Where a facility is connected to both the utility grid and an on-site
generator, the automatic transfer switch (ATS) must ensure the two sources
never supply the load simultaneously — a phase-angle or phase-rotation
mismatch between utility and generator across a shared transformer can
cause a destructive short circuit that damages both. Mechanical ATS units
use break-before-make logic with a brief (10–50 ms) transfer gap; modern
static transfer switches (STS) can achieve near-zero transfer time. The
single-line diagram's transfer logic annotation should state which
approach is used.

## Breaker Selectivity and Coordination

Breaker coordination (selectivity) means that for a fault at any point in
the distribution system, the nearest upstream breaker clears the fault
before any breaker further upstream trips — this confines an outage to the
smallest possible section. Verifying selectivity requires the
manufacturer's time-current characteristic (TCC) curves for each breaker
pair; a coordination study cross-references these curves across the full
distribution tree.
