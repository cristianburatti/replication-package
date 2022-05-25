from cli import CLI
from mine import mine
from generate import generate
from evaluate import evaluate


def main():
    args = CLI()
    if args.action == 'mine':
        mine(args.input)
    elif args.action == 'generate':
        c_type, c_threshold = args.coverage_type, args.coverage_threshold
        generate(args.output, args.measure, args.min, args.max, c_type, c_threshold, args.max_eval_time)
    elif args.action == 'evaluate':
        evaluate(args.input, args.output, args.bleu)


if __name__ == '__main__':
    main()
