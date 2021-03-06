# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A combination of several optimizations targeting XmonDevice."""
from typing import Optional, Callable, cast

from cirq import circuits, ops, devices
from cirq.google import (
    convert_to_xmon_gates,
    merge_rotations,
    merge_interactions,
    eject_full_w,
    eject_z,
    xmon_device)

_TOLERANCE = 1e-5

_OPTIMIZERS = [
    convert_to_xmon_gates.ConvertToXmonGates(),

    merge_interactions.MergeInteractions(tolerance=_TOLERANCE,
                                         allow_partial_czs=False),
    merge_rotations.MergeRotations(tolerance=_TOLERANCE),
    eject_full_w.EjectFullW(tolerance=_TOLERANCE),
    eject_z.EjectZ(tolerance=_TOLERANCE),
    circuits.DropNegligible(tolerance=_TOLERANCE),
]


def optimized_for_xmon(
        circuit: circuits.Circuit,
        new_device: Optional[xmon_device.XmonDevice] = None,
        qubit_map: Callable[[ops.QubitId], devices.GridQubit] =
        lambda e: cast(devices.GridQubit, e),
) -> circuits.Circuit:
    """Optimizes a circuit with XmonDevice in mind.

    Starts by converting the circuit's operations to the xmon gate set, then
    begins merging interactions and rotations, ejecting pi-rotations and phasing
    operations, dropping unnecessary operations, and pushing operations earlier.

    Args:
        circuit: The circuit to optimize.
        new_device: The device the optimized circuit should be targeted at. If
            set to None, the circuit's current device is used.
        qubit_map: Transforms the qubits (e.g. so that they are GridQubits).

    Returns:
        The optimized circuit.
    """
    copy = circuit.copy()
    for optimizer in _OPTIMIZERS:
        optimizer.optimize_circuit(copy)

    return circuits.Circuit.from_ops(
        (op.transform_qubits(qubit_map) for op in copy.all_operations()),
        strategy=circuits.InsertStrategy.EARLIEST,
        device=new_device or copy.device)
