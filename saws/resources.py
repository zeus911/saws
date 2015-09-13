# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
import os
import re
import subprocess
from enum import Enum
from .commands import AwsCommands


class AwsResources(object):
    """Loads and stores AWS resources.

    Attributes:
        * instance_ids: A list of instance ids
        * instance_tag_keys: A set of instance tag keys
        * instance_tag_values: A set of isntance tag values
        * bucket_names: A list of bucket names
        * refresh_instance_ids: A boolean that determines whether to
            refresh instance ids by querying AWS.
        * refresh_instance_tags: A boolean that determines whether to
            refresh instance tags by querying AWS.
        * refresh_bucket_names: A boolean that determines whether to
            refresh bucket names by querying AWS.
        * INSTANCE_IDS_MARKER: A string marking the start of
            instance ids in data/RESOURCES.txt
        * INSTANCE_TAG_KEYS_MARKER: A string marking the start of
            instance tag keys in data/RESOURCES.txt
        * INSTANCE_TAG_VALUES_MARKER: A string marking the start of
            instance tag values in data/RESOURCES.txt
        * BUCKET_NAMES_MARKER: A string marking the start of i
            bucket names in data/RESOURCES.txt
    """

    def __init__(self,
                 refresh_instance_ids=True,
                 refresh_instance_tags=True,
                 refresh_bucket_names=True):
        """Initializes AwsResources.

        Args:
            * refresh_instance_ids: A boolean that determines whether to
                refresh instance ids by querying AWS.
            * refresh_instance_tags: A boolean that determines whether to
                refresh instance tags by querying AWS.
            * refresh_bucket_names: A boolean that determines whether to
                refresh bucket names by querying AWS.

        Returns:
            None.
        """
        self.instance_ids = []
        self.instance_tag_keys = set()
        self.instance_tag_values = set()
        self.bucket_names = []
        self.refresh_instance_ids = refresh_instance_ids
        self.refresh_instance_tags = refresh_instance_tags
        self.refresh_bucket_names = refresh_bucket_names
        self.INSTANCE_IDS_MARKER = '[instance ids]'
        self.INSTANCE_TAG_KEYS_MARKER = '[instance tag keys]'
        self.INSTANCE_TAG_VALUES_MARKER = '[instance tag values]'
        self.BUCKET_NAMES_MARKER = '[bucket names]'

    def refresh(self, force_refresh=False):
        """Refreshes the AWS resources and caches them to a file.

        This function is called on startup.
        If no cache exists, it queries AWS to build the resource lists.
        Pressing the `F5` key will set force_refresh to True, which proceeds
        to refresh the list regardless of whether a cache exists.
        Before returning, it saves the resource lists to cache.

        Args:
            * force_refresh: A boolean determines whether to force a cache
                refresh.  This value is set to True when the user presses `F5`.

        Returns:
            None.
        """
        file_path = os.path.join(AwsCommands.SOURCES_DIR, 'data/RESOURCES.txt')
        if not force_refresh:
            try:
                self.refresh_resources_from_file(file_path)
                print('Loaded resources from cache')
            except IOError:
                print('No resource cache found')
                force_refresh = True
        if force_refresh:
            print('Refreshing resources...')
            if self.refresh_instance_ids:
                print('  Refreshing instance ids...')
                self.query_instance_ids()
            if self.refresh_instance_tags:
                print('  Refreshing instance tags...')
                self.query_instance_tag_keys()
                self.query_instance_tag_values()
            if self.refresh_bucket_names:
                print('  Refreshing bucket names...')
                self.query_bucket_names()
            print('Done refreshing')
        try:
            self.save_resources_to_file(file_path)
        except IOError as e:
            print(e)

    def query_instance_ids(self):
        """Queries and stores instance ids from AWS.

        Args:
            * None.

        Returns:
            None.
        """
        command = 'aws ec2 describe-instances --query "Reservations[].Instances[].[InstanceId]" --output text'
        try:
            result = subprocess.check_output(command,
                                             universal_newlines=True,
                                             shell=True)
            result = re.sub('\n', ' ', result)
            self.instance_ids = result.split()
        except Exception as e:
            print(e)

    def query_instance_tag_keys(self):
        """Queries and stores instance tag keys from AWS.

        Args:
            * None.

        Returns:
            None.
        """
        command = 'aws ec2 describe-instances --filters "Name=tag-key,Values=*" --query Reservations[].Instances[].Tags[].Key --output text'
        try:
            result = subprocess.check_output(command,
                                             universal_newlines=True,
                                             shell=True)
            self.instance_tag_keys = set(result.split('\t'))
        except Exception as e:
            print(e)

    def query_instance_tag_values(self):
        """Queries and stores instance tag values from AWS.

        Args:
            * None

        Returns:
            None.
        """
        command = 'aws ec2 describe-instances --filters "Name=tag-value,Values=*" --query Reservations[].Instances[].Tags[].Value --output text'
        try:
            result = subprocess.check_output(command,
                                             universal_newlines=True,
                                             shell=True)
            self.instance_tag_values = set(result.split('\t'))
        except Exception as e:
            print(e)

    def query_bucket_names(self):
        """Queries and stores bucket names from AWS.

        Args:
            * None

        Returns:
            None
        """
        command = 'aws s3 ls'
        try:
            output = subprocess.check_output(command,
                                             universal_newlines=True,
                                             shell=True)
            self.bucket_names = []
            result_list = output.split('\n')
            for result in result_list:
                try:
                    result = result.split()[-1]
                    self.bucket_names.append(result)
                except:
                    # Ignore blank lines
                    pass
        except Exception as e:
            print(e)

    def refresh_resources_from_file(self, file_path):
        """Refreshes the AWS resources from data/RESOURCES.txt.

        Args:
            * file_path: A string representing the resource file path.

        Returns:
            None.
        """

        class ResType(Enum):
            """Enum specifying the resource type.

            Attributes:
                * INSTANCE_IDS: An int representing instance ids.
                * INSTANCE_TAG_KEYS: An int representing instance tag keys.
                * INSTANCE_TAG_VALUES: An int representing instance tag values.
                * BUCKET_NAMES: An int representing bucket names.
            """

            INSTANCE_IDS, INSTANCE_TAG_KEYS, INSTANCE_TAG_VALUES, \
                BUCKET_NAMES = range(4)

        res_type = ResType.INSTANCE_IDS
        with open(file_path) as fp:
            self.instance_ids = []
            self.instance_tag_keys = set()
            self.instance_tag_values = set()
            self.bucket_names = []
            instance_tag_keys_list = []
            instance_tag_values_list = []
            for line in fp:
                line = re.sub('\n', '', line)
                if line.strip() == '':
                    continue
                elif self.INSTANCE_IDS_MARKER in line:
                    res_type = ResType.INSTANCE_IDS
                    continue
                elif self.INSTANCE_TAG_KEYS_MARKER in line:
                    res_type = ResType.INSTANCE_TAG_KEYS
                    continue
                elif self.INSTANCE_TAG_VALUES_MARKER in line:
                    res_type = ResType.INSTANCE_TAG_VALUES
                    continue
                elif self.BUCKET_NAMES_MARKER in line:
                    res_type = ResType.BUCKET_NAMES
                    continue
                if res_type == ResType.INSTANCE_IDS:
                    self.instance_ids.append(line)
                elif res_type == ResType.INSTANCE_TAG_KEYS:
                    instance_tag_keys_list.append(line)
                elif res_type == ResType.INSTANCE_TAG_VALUES:
                    instance_tag_values_list.append(line)
                elif res_type == ResType.BUCKET_NAMES:
                    self.bucket_names.append(line)
            self.instance_tag_keys = set(instance_tag_keys_list)
            self.instance_tag_values = set(instance_tag_values_list)

    def save_resources_to_file(self, file_path):
        """Saves the AWS resources to data/RESOURCES.txt.

        Args:
            * file_path: A string representing the resource file path.

        Returns:
            None.
        """
        with open(file_path, 'wt') as fp:
            fp.write(self.INSTANCE_IDS_MARKER + '\n')
            for instance_id in self.instance_ids:
                fp.write(instance_id + '\n')
            fp.write(self.INSTANCE_TAG_KEYS_MARKER + '\n')
            for instance_tag_key in self.instance_tag_keys:
                fp.write(instance_tag_key + '\n')
            fp.write(self.INSTANCE_TAG_VALUES_MARKER + '\n')
            for instance_tag_value in self.instance_tag_values:
                fp.write(instance_tag_value + '\n')
            fp.write(self.BUCKET_NAMES_MARKER + '\n')
            for bucket_name in self.bucket_names:
                fp.write(bucket_name + '\n')
