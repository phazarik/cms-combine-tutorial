#!/usr/bin/env bash

combine_home="$HOME/HiggsAnalysis-CombinedLimit"

if [ ! -x "$combine_home/build/bin/combine" ]; then
    echo "ERROR: Combine executable not found:" >&2
    echo "  $combine_home/build/bin/combine" >&2
    unset combine_home
    return 1
fi

if [ -z "${CONDA_PREFIX:-}" ]; then
    echo "ERROR: Activate the Conda analysis environment first." >&2
    unset combine_home
    return 1
fi

if [ ! -f "$CONDA_PREFIX/lib/libcrypto.so" ] ||
   [ ! -f "$CONDA_PREFIX/lib/libssl.so" ]; then
    echo "ERROR: Conda OpenSSL libraries were not found." >&2
    unset combine_home
    return 1
fi

export PATH="$combine_home/build/bin:$combine_home/scripts${PATH:+:$PATH}"
export LD_LIBRARY_PATH="$combine_home/build/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="$combine_home/build/python${PYTHONPATH:+:$PYTHONPATH}"

# Work around the Conda/OpenSSL conflict affecting Python workspace creation.
text2workspace.py() {
    LD_PRELOAD="$CONDA_PREFIX/lib/libcrypto.so:$CONDA_PREFIX/lib/libssl.so" \
        command python3 \
        "$HOME/HiggsAnalysis-CombinedLimit/scripts/text2workspace.py" "$@"
}

# Direct text-datacard input also invokes Python workspace conversion.
combine() {
    LD_PRELOAD="$CONDA_PREFIX/lib/libcrypto.so:$CONDA_PREFIX/lib/libssl.so" \
        command "$HOME/HiggsAnalysis-CombinedLimit/build/bin/combine" "$@"
}

echo "Combine environment loaded from: $combine_home"

unset combine_home
