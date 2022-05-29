import re
from abc import ABC, abstractmethod
from enum import Enum
import javalang
from javalang.tree import *
from collections import defaultdict
from ast import literal_eval


class ExtractorError(Exception):
    pass


class Extractors(Enum):
    none = 'none'
    invoking_signature = 'invoking_signature'
    javadoc = 'javadoc'

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return self.value == other.value


def extractor_factory(extractor_value):
    if extractor_value == Extractors.invoking_signature:
        return InvokingSignatureExtractor()
    elif extractor_value == Extractors.javadoc:
        return JavadocExtractor()

    return NoneExtractor


class ContextExtractor(ABC):
    @abstractmethod
    def extract(self, masked_code, mask, file_content):
        pass

    @abstractmethod
    def baseline(self):
        pass

    @abstractmethod
    def allows_baseline(self):
        pass

    @abstractmethod
    def needs_file_content(self):
        pass

    @staticmethod
    def extract_method_signature(masked_code, mask):
        method_code = masked_code.replace('<extra_id_0>', mask)
        truncated = method_code.split('{')[0]
        method_tree = javalang.parse.parse(f'class ParseC {{ {truncated} {{}} }}')
        clazz = [n for _, n in method_tree.filter(ClassDeclaration)][0]
        if len(clazz.methods) > 0:
            method_signature = ContextExtractor.method_signature(clazz.methods[0])
        else:
            method_signature = ContextExtractor.constructor_signature(clazz.constructors[0])
        method_return, method_name, method_args = method_signature
        return method_return, method_name, method_args

    @staticmethod
    def constructor_signature(node: ConstructorDeclaration):
        arguments = [p.type.name for p in node.parameters]
        return None, node.name, arguments

    @staticmethod
    def method_signature(node: MethodDeclaration):
        return_type = node.return_type.name if node.return_type else 'void'
        arguments = [p.type.name for p in node.parameters]
        return return_type, node.name, arguments

    @staticmethod
    def extract_tree(file_content, *method_signature):
        tree = javalang.parse.parse(file_content)
        classes = [n for _, n in tree.filter(ClassDeclaration)]
        if len(classes) == 1:
            return classes[0]
        for clazz in classes:
            for m in clazz.methods:
                signature = ContextExtractor.method_signature(m)
                if signature == method_signature:
                    return clazz
            for c in clazz.constructors:
                signature = ContextExtractor.constructor_signature(c)
                if signature == method_signature:
                    return clazz
        raise ExtractorError(f'Could not isolate class')


class NoneExtractor(ContextExtractor, ABC):
    def __init__(self):
        self.value = Extractors.none

    def extract(self, masked_code, mask, file_content):
        return ''

    def baseline(self):
        return ''

    def allows_baseline(self):
        return False

    def needs_file_content(self):
        return False


class InvokingSignatureExtractor(ContextExtractor, ABC):
    def __init__(self):
        self.value = Extractors.invoking_signature

    def needs_file_content(self):
        return True

    def baseline(self):
        return '<CONST> <INV> <OTH>'

    def allows_baseline(self):
        return True

    def extract(self, masked_code, mask, file_content):
        method_return, method_name, method_args = ContextExtractor.extract_method_signature(masked_code, mask)
        tree = ContextExtractor.extract_tree(file_content, method_return, method_name, method_args)
        all_methods = InvokingSignatureExtractor.extract_all_methods(tree, method_name, method_args)

        used_methods, constructors = InvokingSignatureExtractor.extract_constructors(tree, method_name, method_args)
        used_methods, invocations = InvokingSignatureExtractor.extract_inside(all_methods, used_methods, masked_code)
        used_methods, invocations = InvokingSignatureExtractor \
            .extract_outside(tree, method_return, method_name, method_args, used_methods, invocations)

        all_methods = [InvokingSignatureExtractor.string_signature(*method) for method in all_methods]
        remaining_methods = ', '.join([m for m in all_methods if m not in used_methods])

        return f'<CONST> {constructors} <INV> {invocations} <OTH> {remaining_methods}'

    @staticmethod
    def string_signature(return_type, name, arguments):
        return f'{return_type + " " if return_type else ""}{name}({", ".join(arguments)})'

    @staticmethod
    def extract_all_methods(tree, method_name, method_args):
        methods = []
        for node in tree.constructors:
            methods.append(ContextExtractor.constructor_signature(node))
        for node in tree.methods:
            methods.append(ContextExtractor.method_signature(node))
        return [m for m in methods if not (m[1] == method_name and m[2] == method_args)]

    @staticmethod
    def extract_constructors(tree, method_name, method_args):
        constructors = []
        for node in tree.constructors:
            args = [p.type.name for p in node.parameters]
            if node.name == method_name and args == method_args:
                continue
            constructors.append(f'{node.name}({", ".join(args)})')
        return constructors, ', '.join(constructors)

    @staticmethod
    def extract_inside(all_methods, used_methods, masked_code):
        invocations = []

        for method_return, method_name, method_args in all_methods:
            string_method = InvokingSignatureExtractor.string_signature(method_return, method_name, method_args)
            if string_method in used_methods:
                continue

            matches = re.finditer(f'{method_name}\\s*\\(', masked_code)
            matches = [(m.start(0), m.end(0)) for m in matches]
            args = set()
            for start, end in matches:
                i = end
                par_count = 1
                arg_count = 0 if (i >= len(masked_code) or masked_code[i] == ')') else 1
                while i < len(masked_code) and par_count > 0:
                    if masked_code[i] == '(':
                        par_count += 1
                    elif masked_code[i] == ')':
                        par_count -= 1
                    elif masked_code[i] == ',' and par_count == 1:
                        arg_count += 1
                    i += 1
                if par_count != 0:
                    continue

                args.add(arg_count)
            if len(method_args) in args:
                used_methods.append(string_method)
                invocations.append(string_method)

        return used_methods, invocations

    @staticmethod
    def extract_outside(tree, method_return, method_name, method_args, used_methods, invocations):
        method_signature = InvokingSignatureExtractor.string_signature(method_return, method_name, method_args)

        for node in tree.methods:
            return_type, name, args = ContextExtractor.method_signature(node)
            signature = InvokingSignatureExtractor.string_signature(return_type, name, args)
            if signature in used_methods or signature == method_signature:
                continue

            for _, invocation in node.filter(MethodInvocation):
                if invocation.member == method_name and len(invocation.arguments) == len(method_args):
                    invocations.append(signature)
                    used_methods.append(signature)
                    break

        return used_methods, ', '.join(invocations)


class JavadocExtractor(ContextExtractor, ABC):
    def __init__(self):
        self.value = Extractors.javadoc

    def needs_file_content(self):
        return True

    def baseline(self):
        return None

    def allows_baseline(self):
        return False

    def extract(self, masked_code, mask, file_content):
        method_signature = ContextExtractor.extract_method_signature(masked_code, mask)
        tree = ContextExtractor.extract_tree(file_content, *method_signature)

        if method_signature[0]:
            methods = tree.methods
            signature_extractor = ContextExtractor.method_signature
        else:
            methods = tree.constructors
            signature_extractor = ContextExtractor.constructor_signature

        methods = [method for method in methods if signature_extractor(method) == method_signature]
        if len(methods) != 1:
            raise ExtractorError(f'Could not isolate method')

        method = methods[0]
        javadoc = method.documentation
        if javadoc is None:
            raise ExtractorError(f'No javadoc found')
        return f'<SEP> {javadoc}'
