"""Resume untouched cases; avoid a post-route report assertion in setup only."""
import run_native_cpu_slices as slices
import run_native_cpu_study as study


def main():
    original=study.cpu_command
    def command(binary,case,directory,variant,workers,cache=None,iterations=200):
        result=original(binary,case,directory,variant,workers,cache,iterations)
        if directory.name.endswith(('_cache_original','_cache_optimized')):
            assert iterations==1 and cache is None
            study.set_option(result,'--generate_rr_node_overuse_report','off')
        return result
    study.cpu_command=command
    slices.main()


if __name__=='__main__':main()
