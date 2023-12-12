import collections
import re

from ansible.errors import AnsibleFilterError


def consensus(pipe_in: dict[str], set: bool = False, msg=""):
    apply = FilterModule.xset if set else id
    [head, *tail] = map(apply, pipe_in.values())
    if not all(head == x for x in tail):
        raise AnsibleFilterError(msg or "No consensus", pipe_in)
    return head


def split2multidict(pipe_in, sep=None):
    result = collections.defaultdict(list)
    for key, val in map(lambda line: line.split(sep, 1), pipe_in):
        result[key].append(val)
    return result


def regex_replace(pipe_in, pattern, repl, count=0, require_n=0):
    result, actual_n = re.subn(pattern, repl, pipe_in, count=count)
    if require_n not in {0, actual_n}:
        raise AnsibleFilterError("unexpected substitution count")
    return result


class FilterModule(object):
    xset = set

    def filters(self):
        return {
            "consensus": consensus,
            "split2multidict": split2multidict,
            "regex_replace": regex_replace,
        }
