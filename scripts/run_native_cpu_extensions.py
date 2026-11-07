"""Add explicit VPR baseline options without changing the frozen main runner."""
import run_native_cpu_study as study


base_command = study.cpu_command


def extended_command(binary, case, directory, variant, workers, cache=None, iterations=200):
    command = base_command(binary, case, directory, variant, workers, cache, iterations)
    for option, value in variant.get('extra_options', {}).items():
        study.set_option(command, option, value)
    return command


if __name__ == '__main__':
    study.cpu_command = extended_command
    study.main()
