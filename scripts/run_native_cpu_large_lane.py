"""Large-case wrapper: clean inherited experiment flags, preserve frozen runner."""
import run_native_cpu_slices as slices
import run_native_cpu_study as study


def main():
    original_env, original_command = study.vpr_environment, study.cpu_command

    def environment(runtime):
        return {k: v for k, v in original_env(runtime).items()
                if not k.startswith(('VPR_CPU_', 'VPR_HYBRID_', 'H3D_GPU_'))}

    def command(binary, case, directory, variant, workers, cache=None, iterations=200):
        result = original_command(binary, case, directory, variant, workers, cache, iterations)
        if directory.name.endswith(('_cache_original', '_cache_optimized')):
            assert iterations == 1 and cache is None
            study.set_option(result, '--generate_rr_node_overuse_report', 'off')
        return result

    study.vpr_environment = environment
    study.cpu_command = command
    slices.main()


if __name__ == '__main__':
    main()
