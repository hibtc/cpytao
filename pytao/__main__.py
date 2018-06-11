import sys
import pytao.tao_pipe as tao

tao.set_init_args(" ".join(sys.argv[1:]))
while True:
    line = sys.stdin.readline().decode('utf-8')
    if not line:
        break
    print(line)
    tao.command(line.strip())
