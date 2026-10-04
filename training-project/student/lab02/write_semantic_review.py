"""Record the student's own findings with hashes of the exact reviewed artifacts."""

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from learning_project.lab02 import SOURCE_RELATIVE_PATH, _validate_review_bindings


def ask(prompt: str) -> str:
    print(prompt)
    answer = input('> ').strip()
    if not answer:
        raise ValueError('An empty finding cannot be recorded. Run Review again.')
    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', type=Path, required=True)
    parser.add_argument('--report-dir', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--by', required=True)
    args = parser.parse_args()
    import re

    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.run_id):
        raise ValueError('Run ID must be a lowercase slug.')
    if not args.by.strip():
        raise ValueError('The reviewer identifier cannot be empty.')
    proposal_id = 'lab02-structured-output-' + args.run_id
    proposal_path = args.vault / 'proposals' / f'{proposal_id}.md'
    validation_path = args.report_dir / 'runs' / args.run_id / 'validation-result.json'
    proposal_bytes = proposal_path.read_bytes()
    validation_bytes = validation_path.read_bytes()
    validation = json.loads(validation_bytes)
    proposal_sha = hashlib.sha256(proposal_bytes).hexdigest()
    if not validation.get('valid') or validation.get('proposal_id') != proposal_id:
        raise ValueError('The selected candidate has not passed validation.')
    if validation.get('proposal_sha256') != proposal_sha:
        raise ValueError('The proposal changed after validation; do not overwrite evidence.')

    print('\nREGISTERED SOURCE\n')
    print((args.vault / SOURCE_RELATIVE_PATH).read_text(encoding='utf-8'))
    print('\nSELECTED CANDIDATE\n')
    print(proposal_bytes.decode('utf-8'))
    print('\nWrite your own findings in Ukrainian. No approval is recorded by this script.\n')
    definition = ask('Q1: Does the definition accurately represent Structured Output in the source? Why?')
    quotes = ask('Q2: Explain how each of the three distinct exact quotes supports its claim_kind.')
    gates = ask('Q3: Are syntax, deterministic invariants, and human semantic judgment kept separate?')
    authority = ask('Q4: Does the model only propose, the human decide, and a separate apply write accepted state?')
    unsupported = ask('Q5: Does the candidate add meaning not supported by the source? Explain.')
    learning = ask('Q6: Are tags and key points useful for learning, without provider metadata? Explain.')
    verdict = ask('Verdict: type acceptable or unsupported after checking all six answers.')
    if verdict not in {'acceptable', 'unsupported'}:
        raise ValueError('Verdict must be acceptable or unsupported.')
    conclusion = ask('Explain why these findings justify this verdict.')

    review = {
        'schema_version': '1.0',
        'review_id': f'{proposal_id}-review',
        'proposal_id': proposal_id,
        'proposal_sha256': proposal_sha,
        'validation_id': validation['validation_id'],
        'validation_sha256': hashlib.sha256(validation_bytes).hexdigest(),
        'findings': {
            'definition': definition,
            'control_gates': quotes + '\n' + gates,
            'authority_boundary': authority,
        },
        'rationale': unsupported + '\n' + learning + '\n' + conclusion,
        'verdict': verdict,
        'reviewed_by': args.by.strip(),
    }
    _validate_review_bindings(
        proposal_id=proposal_id,
        proposal_sha256=proposal_sha,
        validation=validation,
        validation_bytes=validation_bytes,
        review=review,
    )
    if proposal_path.read_bytes() != proposal_bytes or validation_path.read_bytes() != validation_bytes:
        raise ValueError('Reviewed files changed during review. No review was saved.')
    if verdict == 'acceptable':
        output = args.report_dir / 'semantic-review.yaml'
    else:
        output = args.report_dir / 'reviews' / f'{proposal_id}.yaml'
    output.parent.mkdir(parents=True, exist_ok=True)
    # The same review must never be overwritten after a bound decision.
    with output.open('xb') as stream:
        stream.write(yaml.safe_dump(review, sort_keys=False, allow_unicode=True).encode('utf-8'))
    print(f'Saved your {verdict} review to {output}. No decision or apply was executed.')


if __name__ == '__main__':
    main()
