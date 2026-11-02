"""
Data-skew simulator + salting fix, in plain Python (no Spark needed).

Three keys (1, 2, 3) with 1150 rows total, shown under three skew profiles:
  extreme   1 -> 1000, 2 -> 50,  3 -> 100
  moderate  1 -> 700,  2 -> 250, 3 -> 200
  okay      1 -> 400,  2 -> 380, 3 -> 370

Watch the "okay" profile: the keys are almost even, yet one partition still gets
750 rows, because keys 2 and 3 happen to hash to the same partition. With only a
handful of distinct keys, even balanced keys do not give you balanced partitions.

For each profile it shows:
  1. the key distribution (what the data looks like)
  2. partition load with a plain hash partitioner:  pmod(hash(key), numPartitions)
  3. partition load after salting:                  pmod(hash(f"{key}_{salt}"), numPartitions)

Spark hashes with murmur3_32; here we use crc32, which is deterministic across
runs and good enough to show the mechanics. (Python's builtin hash() for strings
is randomized per process by PYTHONHASHSEED, so it is NOT used.)

Usage:
    python skew_salting_demo.py
    python skew_salting_demo.py --partitions 8 --salt-factor 6
"""

import argparse
from collections import Counter
from zlib import crc32

SCENARIOS = {
    "extreme": {1: 1000, 2: 50, 3: 100},
    "moderate": {1: 700, 2: 250, 3: 200},
    "okay": {1: 400, 2: 380, 3: 370},
}


def spark_hash(key) -> int:
    """Deterministic 32-bit hash of the key's string form (stand-in for murmur3_32)."""
    return crc32(str(key).encode("utf-8"))


def pmod(value: int, divisor: int) -> int:
    """Spark's pmod: always a non-negative partition id."""
    return ((value % divisor) + divisor) % divisor


def partition_of(key, num_partitions: int) -> int:
    return pmod(spark_hash(key), num_partitions)


def bar(count: int, total: int, width: int = 40) -> str:
    filled = 0 if total == 0 else round(width * count / total)
    return "#" * filled + "." * (width - filled)


def skew_ratio(counts) -> float:
    """max / mean load. 1.0 == perfectly even; higher == more skewed."""
    values = list(counts)
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return max(values) / mean if mean else 0.0


def print_distribution(title: str, counts: Counter, total: int, label: str) -> None:
    print(f"  {title}")
    for k in sorted(counts):
        c = counts[k]
        pct = 100 * c / total
        print(f"    {label} {str(k):<10} {c:>5} rows ({pct:5.1f}%)  {bar(c, total)}")


def explode_rows(key_counts: dict):
    """Turn {key: count} into the actual row stream, like a real dataset."""
    for key, count in key_counts.items():
        for i in range(count):
            yield key, i  # i == row index within the key, used to spread salts


def run_scenario(name: str, key_counts: dict, num_partitions: int, salt_factor: int) -> None:
    total = sum(key_counts.values())

    print("=" * 78)
    print(f"SCENARIO: {name.upper()}   (total rows = {total})")
    print("=" * 78)

    # ---- 1. key distribution -------------------------------------------------
    print_distribution("Key distribution in the data", Counter(key_counts), total, "key")
    print(f"    key-level skew ratio (max/mean) = {skew_ratio(key_counts.values()):.2f}")
    print()

    # ---- 2. no salting -------------------------------------------------------
    no_salt = Counter({p: 0 for p in range(num_partitions)})
    for key, _ in explode_rows(key_counts):
        no_salt[partition_of(key, num_partitions)] += 1

    print(f"  WITHOUT salting -> pmod(hash(key), {num_partitions})")
    for key in sorted(key_counts):
        print(
            f"    key {key}: hash={spark_hash(key):>12} -> "
            f"pmod {num_partitions} = partition {partition_of(key, num_partitions)}"
            f"  ({key_counts[key]} rows land there)"
        )
    print()
    print_distribution("Partition load", no_salt, total, "partition")
    print(f"    partition skew ratio (max/mean) = {skew_ratio(no_salt.values()):.2f}")
    print(f"    heaviest partition = {max(no_salt.values())} rows, "
          f"empty partitions = {sum(1 for v in no_salt.values() if v == 0)}")
    print()

    # ---- 3. with salting -----------------------------------------------------
    salted = Counter({p: 0 for p in range(num_partitions)})
    salted_keys = Counter()
    for key, row_idx in explode_rows(key_counts):
        salt = row_idx % salt_factor              # round-robin salt, 0..salt_factor-1
        composite = f"{key}_{salt}"               # e.g. "1_1"
        salted[partition_of(composite, num_partitions)] += 1
        salted_keys[composite] += 1

    print(f"  WITH salting -> pmod(hash(f\"{{key}}_{{salt}}\"), {num_partitions}), "
          f"salt in 0..{salt_factor - 1}")
    max_shown = 4
    for key in sorted(key_counts):
        for salt in range(min(salt_factor, max_shown)):
            composite = f"{key}_{salt}"
            print(
                f"    \"{composite}\": hash={spark_hash(composite):>12} -> "
                f"partition {partition_of(composite, num_partitions)}"
                f"  ({salted_keys[composite]} rows)"
            )
        if salt_factor > max_shown:
            print(f"    ... and {salt_factor - max_shown} more salts for key {key}")
    print()
    print_distribution("Partition load", salted, total, "partition")
    print(f"    partition skew ratio (max/mean) = {skew_ratio(salted.values()):.2f}")
    print(f"    heaviest partition = {max(salted.values())} rows, "
          f"empty partitions = {sum(1 for v in salted.values() if v == 0)}")
    print()

    # ---- verdict -------------------------------------------------------------
    before, after = max(no_salt.values()), max(salted.values())
    ideal = total / num_partitions
    print(f"  RESULT: heaviest partition {before} -> {after} rows "
          f"(ideal even split = {ideal:.0f}). "
          f"Straggler task shrinks by {100 * (before - after) / before:.0f}%.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--partitions", type=int, default=6,
                        help="number of shuffle partitions (default: 6)")
    parser.add_argument("--salt-factor", type=int, default=12,
                        help="how many salt values per key (default: 12)")
    parser.add_argument("--scenario", choices=list(SCENARIOS) + ["all"], default="all",
                        help="which skew profile to run (default: all)")
    args = parser.parse_args()

    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]

    print()
    print(f"partitions = {args.partitions}, salt factor = {args.salt_factor}, "
          f"hash = crc32(str(key))")
    print()
    for name in names:
        run_scenario(name, SCENARIOS[name], args.partitions, args.salt_factor)

    print("=" * 78)
    print("SUMMARY (heaviest partition, lower is better)")
    print("=" * 78)
    print(f"  {'scenario':<10} {'key skew':>9} {'no salt':>9} {'salted':>9} {'ideal':>9}")
    for name in names:
        key_counts = SCENARIOS[name]
        total = sum(key_counts.values())
        no_salt = Counter({p: 0 for p in range(args.partitions)})
        salted = Counter({p: 0 for p in range(args.partitions)})
        for key, row_idx in explode_rows(key_counts):
            no_salt[partition_of(key, args.partitions)] += 1
            salted[partition_of(f"{key}_{row_idx % args.salt_factor}", args.partitions)] += 1
        print(f"  {name:<10} {skew_ratio(key_counts.values()):>9.2f} "
              f"{max(no_salt.values()):>9} {max(salted.values()):>9} "
              f"{total / args.partitions:>9.0f}")
    print()
    print("  Notes:")
    print("  - Salting splits one hot key into N sub-keys so N tasks share the work.")
    print("  - In a join you must explode the small side into all N salts (explode(array(0..N-1)))")
    print("    or the salted rows find no match and you lose results.")
    print("  - Salting cannot beat the ideal split: with few distinct keys, sub-keys still")
    print("    collide onto the same partition. Raise --salt-factor to smooth that out.")
    print("  - Even key counts != even partitions: see the 'okay' row, where keys 2 and 3")
    print("    hash to the same partition and 750 rows pile onto one task.")
    print()


if __name__ == "__main__":
    main()
