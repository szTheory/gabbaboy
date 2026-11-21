# gbmicrotest div_inc_timing_a source and output

Pinned source: https://github.com/aappleby/gbmicrotest/tree/463eb6bc0fe31d61781ef63060ad6d74090c0255 (tree 9b692d1a028beea00a9fc08b89bc6160dd268efa).

The only runtime payload is the bootless derivative SHA-256 53b0624af64524fe7cdf9b0aed3456ca60c7b30fe25cd5202b6b77855f57ffa8.

The case declares pass - dmg, resets DIV, executes 60 NOPs, and requires DIV=0. This supports DMG-CPU-B software diagnostic scope only.

The complete pinned root MIT notice is included. The pinned README lists prebuilt ROMs in bin/ but does not explicitly state binary-output terms. Applying the MIT Software grant and OSI compiled-form/derived-work language to this single modified copy is a bounded interpretation, not an upstream explicit ROM-output statement or legal certainty. It excludes the original ROM, removed Nintendo logo bytes, the other 512 ROMs, and other sources.

The original ROM and all Nintendo logo bytes are excluded. No WLA-DX build or hardware claim is made.
