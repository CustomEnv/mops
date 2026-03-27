import os
import re
import shutil
import sys
import zipfile
import base64
import argparse
import json
from io import BytesIO
from os.path import join
from pathlib import Path

import requests
from PIL import Image


REPO = 'CustomEnv/mops'
ARTIFACT_NAME = 'allure-report'


class Args:

    def __init__(self, parser):
        launched_args = parser.parse_args()
        self.commit_sha = launched_args.commit_sha
        self.output_dir = launched_args.output_dir
        self.token = launched_args.token


class UpdateReferences:

    def __init__(self, directory):
        self.directory = self._get_project_path(directory)
        self.ref_directory =  self._get_reference_screenshots_path()

        if not os.path.exists(self.ref_directory ):
            os.makedirs(self.ref_directory )

    def _get_project_path(self, suffix: str = ''):
        return str(Path(os.path.dirname(__file__)).parent.parent.joinpath(suffix))

    def _get_reference_screenshots_path(self):
        base_path = os.path.dirname(__file__) or '.'
        return base_path + '/visual/reference/'

    def _collect_screenshot_names_and_files(self):
        sources = {}

        for root, _, files in os.walk(self.directory):
            for filename in files:
                if 'result.json' not in filename:
                    continue
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)  # Parse allure tests case file
                    attachments = data.get('attachments', {})
                    if attachments:
                        for attachment in attachments:
                            if attachment['type'] == 'application/vnd.allure.image.diff':
                                _screenshot_name = attachment['name'].replace('diff_for_', '') + '.png'
                                sources[_screenshot_name] = attachment['source']

        return sources

    def replace_references(self):
        for screenshot_name, file_name in self._collect_screenshot_names_and_files().items():
            with open(f'{self.directory}/allure-report/{file_name}', 'r', encoding='utf-8') as file:
                data = json.load(file)
                image_bytes = base64.b64decode(data['actual'].replace('data:image/png;base64,', ''))
                image = Image.open(BytesIO(image_bytes))  # noqa
                image.save(join(self.ref_directory, screenshot_name))
                print('Replaced: ', screenshot_name)


class DownloadArtifacts:

    def __init__(self, launch_args: Args):
        self.launch_args = launch_args
        self.updated_artifact_names = []

    def _drop_python_version(self, artefact_name):
        return re.sub(r"-\b\d{2,3}\b", "", artefact_name).strip()

    def _is_already_updated(self, artifact_name):
        status = artifact_name in self.updated_artifact_names
        if status:
            print(f'{artifact_name} already exists in uploaded artifacts: {self.updated_artifact_names}')
        return status

    def download_artefact_and_replace_references(self):

        assert self.launch_args.token, 'Env variable GH_TOKEN or --token arg required'
        os.makedirs(self.launch_args.output_dir, exist_ok=True)
        reference_updater = UpdateReferences(self.launch_args.output_dir)
        bae_api_url = 'https://api.github.com'
        repos_url = f'{bae_api_url}/repos'

        try:
            print(f"Finding PR associated with commit {self.launch_args.commit_sha}...")
            pr_number = self._api_request(f"{bae_api_url}/search/issues?q=repo:{REPO}+sha:{self.launch_args.commit_sha}+is:pr")['items'][0]['number']
            branch_name = self._api_request(f"{repos_url}/{REPO}/pulls/{pr_number}")['head']['ref']
            runs_response = self._api_request(f"{repos_url}/{REPO}/actions/runs?per_page=100&branch={branch_name}&head_sha={self.launch_args.commit_sha}")
            run_ids = [run["id"] for run in runs_response.get("workflow_runs", [])]
            for run_id in run_ids:
                artifacts_response = self._api_request(f"{repos_url}/{REPO}/actions/runs/{run_id}/artifacts")
                for artifact in artifacts_response.get("artifacts", []):
                    artifact_name = self._drop_python_version(artifact["name"])
                    if (
                            ARTIFACT_NAME in artifact_name
                            and self.launch_args.commit_sha == artifact['workflow_run']['head_sha']
                            and not self._is_already_updated(artifact_name)
                    ):
                        download_url = artifact["archive_download_url"]
                        self._download_and_extract_artifact(download_url)
                        try:
                            reference_updater.replace_references()
                            self.updated_artifact_names.append(artifact_name)
                        except Exception as exc:
                            raise exc
                        finally:
                            if os.path.exists(self.launch_args.output_dir):
                                print('Cleaning up directory: ', self.launch_args.output_dir)
                                shutil.rmtree(f'{self.launch_args.output_dir}/{ARTIFACT_NAME}')

                        print()


        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")

        if not self.updated_artifact_names:
            sys.exit(f'No any artifacts were updated for "{self.launch_args.commit_sha}" commit')

    def _api_request(self, url):
        headers = {
            "Authorization": f"token {self.launch_args.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def _download_and_extract_artifact(self, download_url):
        """Downloads and extracts a ZIP artifact."""
        zip_path = os.path.join(self.launch_args.output_dir, f"{ARTIFACT_NAME}.zip")
        extract_path = os.path.join(self.launch_args.output_dir, ARTIFACT_NAME)

        try:
            print(f"Downloading artifact to {zip_path}...")
            headers = {"Authorization": f"token {self.launch_args.token}"}
            response = requests.get(download_url, headers=headers, stream=True, allow_redirects=True)
            response.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"Extracting artifact to {extract_path}...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            os.remove(zip_path) # Remove zip file after extraction

            print(f"Artifact extracted successfully to {extract_path}.")
            return extract_path

        except requests.exceptions.RequestException as e:
            print(f"Error downloading artifact: {e}")
            return None
        except zipfile.BadZipFile as e:
            print(f"Error extracting artifact (invalid ZIP file): {e}")
            os.remove(zip_path)
            return None
        except Exception as e:
            print(f"An unexpected error occurred during artifact processing: {e}")
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download GitHub Actions artifacts from a PR based on commit SHA.")
    parser.add_argument("commit_sha", help="Commit SHA")
    parser.add_argument("-o", "--output-dir", default="./artifacts", help="Output directory (default: ./artifacts)")
    parser.add_argument("-t", "--token", default=os.environ.get('GH_TOKEN'), help="GitHub personal access token (or set GITHUB_TOKEN environment variable)")
    DownloadArtifacts(Args(parser)).download_artefact_and_replace_references()