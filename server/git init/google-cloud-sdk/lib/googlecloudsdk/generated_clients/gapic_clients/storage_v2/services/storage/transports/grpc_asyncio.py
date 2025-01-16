# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import warnings
from typing import Awaitable, Callable, Dict, Optional, Sequence, Tuple, Union

from google.api_core import gapic_v1
from google.api_core import grpc_helpers_async
from google.api_core import exceptions as core_exceptions
from google.api_core import retry_async as retries
from google.auth import credentials as ga_credentials   # type: ignore
from google.auth.transport.grpc import SslCredentials  # type: ignore

import grpc                        # type: ignore
from grpc.experimental import aio  # type: ignore

from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.storage_v2.types import storage
from .base import StorageTransport, DEFAULT_CLIENT_INFO
from .grpc import StorageGrpcTransport


class StorageGrpcAsyncIOTransport(StorageTransport):
    """gRPC AsyncIO backend transport for Storage.

    API Overview and Naming Syntax
    ------------------------------

    The Cloud Storage gRPC API allows applications to read and write
    data through the abstractions of buckets and objects. For a
    description of these abstractions please see
    https://cloud.google.com/storage/docs.

    Resources are named as follows:

    -  Projects are referred to as they are defined by the Resource
       Manager API, using strings like ``projects/123456`` or
       ``projects/my-string-id``.

    -  Buckets are named using string names of the form:
       ``projects/{project}/buckets/{bucket}`` For globally unique
       buckets, ``_`` may be substituted for the project.

    -  Objects are uniquely identified by their name along with the name
       of the bucket they belong to, as separate strings in this API.
       For example:

       ReadObjectRequest { bucket: 'projects/_/buckets/my-bucket'
       object: 'my-object' } Note that object names can contain ``/``
       characters, which are treated as any other character (no special
       directory semantics).

    This class defines the same methods as the primary client, so the
    primary client can load the underlying transport implementation
    and call it.

    It sends protocol buffers over the wire using gRPC (which is built on
    top of HTTP/2); the ``grpcio`` package must be installed.
    """

    _grpc_channel: aio.Channel
    _stubs: Dict[str, Callable] = {}

    @classmethod
    def create_channel(cls,
                       host: str = 'storage.googleapis.com',
                       credentials: Optional[ga_credentials.Credentials] = None,
                       credentials_file: Optional[str] = None,
                       scopes: Optional[Sequence[str]] = None,
                       quota_project_id: Optional[str] = None,
                       **kwargs) -> aio.Channel:
        """Create and return a gRPC AsyncIO channel object.
        Args:
            host (Optional[str]): The host for the channel to use.
            credentials (Optional[~.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify this application to the service. If
                none are specified, the client will attempt to ascertain
                the credentials from the environment.
            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
            scopes (Optional[Sequence[str]]): A optional list of scopes needed for this
                service. These are only used when credentials are not specified and
                are passed to :func:`google.auth.default`.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            kwargs (Optional[dict]): Keyword arguments, which are passed to the
                channel creation.
        Returns:
            aio.Channel: A gRPC AsyncIO channel object.
        """

        return grpc_helpers_async.create_channel(
            host,
            credentials=credentials,
            credentials_file=credentials_file,
            quota_project_id=quota_project_id,
            default_scopes=cls.AUTH_SCOPES,
            scopes=scopes,
            default_host=cls.DEFAULT_HOST,
            **kwargs
        )

    def __init__(self, *,
            host: str = 'storage.googleapis.com',
            credentials: Optional[ga_credentials.Credentials] = None,
            credentials_file: Optional[str] = None,
            scopes: Optional[Sequence[str]] = None,
            channel: Optional[Union[aio.Channel, Callable[..., aio.Channel]]] = None,
            api_mtls_endpoint: Optional[str] = None,
            client_cert_source: Optional[Callable[[], Tuple[bytes, bytes]]] = None,
            ssl_channel_credentials: Optional[grpc.ChannelCredentials] = None,
            client_cert_source_for_mtls: Optional[Callable[[], Tuple[bytes, bytes]]] = None,
            quota_project_id: Optional[str] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            always_use_jwt_access: Optional[bool] = False,
            api_audience: Optional[str] = None,
            ) -> None:
        """Instantiate the transport.

        Args:
            host (Optional[str]):
                 The hostname to connect to (default: 'storage.googleapis.com').
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
                This argument is ignored if a ``channel`` instance is provided.
            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is ignored if a ``channel`` instance is provided.
            scopes (Optional[Sequence[str]]): A optional list of scopes needed for this
                service. These are only used when credentials are not specified and
                are passed to :func:`google.auth.default`.
            channel (Optional[Union[aio.Channel, Callable[..., aio.Channel]]]):
                A ``Channel`` instance through which to make calls, or a Callable
                that constructs and returns one. If set to None, ``self.create_channel``
                is used to create the channel. If a Callable is given, it will be called
                with the same arguments as used in ``self.create_channel``.
            api_mtls_endpoint (Optional[str]): Deprecated. The mutual TLS endpoint.
                If provided, it overrides the ``host`` argument and tries to create
                a mutual TLS channel with client SSL credentials from
                ``client_cert_source`` or application default SSL credentials.
            client_cert_source (Optional[Callable[[], Tuple[bytes, bytes]]]):
                Deprecated. A callback to provide client SSL certificate bytes and
                private key bytes, both in PEM format. It is ignored if
                ``api_mtls_endpoint`` is None.
            ssl_channel_credentials (grpc.ChannelCredentials): SSL credentials
                for the grpc channel. It is ignored if a ``channel`` instance is provided.
            client_cert_source_for_mtls (Optional[Callable[[], Tuple[bytes, bytes]]]):
                A callback to provide client certificate bytes and private key bytes,
                both in PEM format. It is used to configure a mutual TLS channel. It is
                ignored if a ``channel`` instance or ``ssl_channel_credentials`` is provided.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you're developing
                your own client library.
            always_use_jwt_access (Optional[bool]): Whether self signed JWT should
                be used for service account credentials.

        Raises:
            google.auth.exceptions.MutualTlsChannelError: If mutual TLS transport
              creation failed for any reason.
          google.api_core.exceptions.DuplicateCredentialArgs: If both ``credentials``
              and ``credentials_file`` are passed.
        """
        self._grpc_channel = None
        self._ssl_channel_credentials = ssl_channel_credentials
        self._stubs: Dict[str, Callable] = {}

        if api_mtls_endpoint:
            warnings.warn("api_mtls_endpoint is deprecated", DeprecationWarning)
        if client_cert_source:
            warnings.warn("client_cert_source is deprecated", DeprecationWarning)

        if isinstance(channel, aio.Channel):
            # Ignore credentials if a channel was passed.
            credentials = False
            # If a channel was explicitly provided, set it.
            self._grpc_channel = channel
            self._ssl_channel_credentials = None
        else:
            if api_mtls_endpoint:
                host = api_mtls_endpoint

                # Create SSL credentials with client_cert_source or application
                # default SSL credentials.
                if client_cert_source:
                    cert, key = client_cert_source()
                    self._ssl_channel_credentials = grpc.ssl_channel_credentials(
                        certificate_chain=cert, private_key=key
                    )
                else:
                    self._ssl_channel_credentials = SslCredentials().ssl_credentials

            else:
                if client_cert_source_for_mtls and not ssl_channel_credentials:
                    cert, key = client_cert_source_for_mtls()
                    self._ssl_channel_credentials = grpc.ssl_channel_credentials(
                        certificate_chain=cert, private_key=key
                    )

        # The base transport sets the host, credentials and scopes
        super().__init__(
            host=host,
            credentials=credentials,
            credentials_file=credentials_file,
            scopes=scopes,
            quota_project_id=quota_project_id,
            client_info=client_info,
            always_use_jwt_access=always_use_jwt_access,
            api_audience=api_audience,
        )

        if not self._grpc_channel:
            # initialize with the provided callable or the default channel
            channel_init = channel or type(self).create_channel
            self._grpc_channel = channel_init(
                self._host,
                # use the credentials which are saved
                credentials=self._credentials,
                # Set ``credentials_file`` to ``None`` here as
                # the credentials that we saved earlier should be used.
                credentials_file=None,
                scopes=self._scopes,
                ssl_credentials=self._ssl_channel_credentials,
                quota_project_id=quota_project_id,
                options=[
                    ("grpc.max_send_message_length", -1),
                    ("grpc.max_receive_message_length", -1),
                ],
            )

        # Wrap messages. This must be done after self._grpc_channel exists
        self._prep_wrapped_messages(client_info)

    @property
    def grpc_channel(self) -> aio.Channel:
        """Create the channel designed to connect to this service.

        This property caches on the instance; repeated calls return
        the same channel.
        """
        # Return the channel from cache.
        return self._grpc_channel

    @property
    def delete_bucket(self) -> Callable[
            [storage.DeleteBucketRequest],
            Awaitable[empty_pb2.Empty]]:
        r"""Return a callable for the delete bucket method over gRPC.

        Permanently deletes an empty bucket.

        Returns:
            Callable[[~.DeleteBucketRequest],
                    Awaitable[~.Empty]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'delete_bucket' not in self._stubs:
            self._stubs['delete_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/DeleteBucket',
                request_serializer=storage.DeleteBucketRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs['delete_bucket']

    @property
    def get_bucket(self) -> Callable[
            [storage.GetBucketRequest],
            Awaitable[storage.Bucket]]:
        r"""Return a callable for the get bucket method over gRPC.

        Returns metadata for the specified bucket.

        Returns:
            Callable[[~.GetBucketRequest],
                    Awaitable[~.Bucket]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_bucket' not in self._stubs:
            self._stubs['get_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetBucket',
                request_serializer=storage.GetBucketRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['get_bucket']

    @property
    def create_bucket(self) -> Callable[
            [storage.CreateBucketRequest],
            Awaitable[storage.Bucket]]:
        r"""Return a callable for the create bucket method over gRPC.

        Creates a new bucket.

        Returns:
            Callable[[~.CreateBucketRequest],
                    Awaitable[~.Bucket]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'create_bucket' not in self._stubs:
            self._stubs['create_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/CreateBucket',
                request_serializer=storage.CreateBucketRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['create_bucket']

    @property
    def list_buckets(self) -> Callable[
            [storage.ListBucketsRequest],
            Awaitable[storage.ListBucketsResponse]]:
        r"""Return a callable for the list buckets method over gRPC.

        Retrieves a list of buckets for a given project.

        Returns:
            Callable[[~.ListBucketsRequest],
                    Awaitable[~.ListBucketsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'list_buckets' not in self._stubs:
            self._stubs['list_buckets'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ListBuckets',
                request_serializer=storage.ListBucketsRequest.serialize,
                response_deserializer=storage.ListBucketsResponse.deserialize,
            )
        return self._stubs['list_buckets']

    @property
    def lock_bucket_retention_policy(self) -> Callable[
            [storage.LockBucketRetentionPolicyRequest],
            Awaitable[storage.Bucket]]:
        r"""Return a callable for the lock bucket retention policy method over gRPC.

        Locks retention policy on a bucket.

        Returns:
            Callable[[~.LockBucketRetentionPolicyRequest],
                    Awaitable[~.Bucket]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'lock_bucket_retention_policy' not in self._stubs:
            self._stubs['lock_bucket_retention_policy'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/LockBucketRetentionPolicy',
                request_serializer=storage.LockBucketRetentionPolicyRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['lock_bucket_retention_policy']

    @property
    def get_iam_policy(self) -> Callable[
            [iam_policy_pb2.GetIamPolicyRequest],
            Awaitable[policy_pb2.Policy]]:
        r"""Return a callable for the get iam policy method over gRPC.

        Gets the IAM policy for a specified bucket. The ``resource``
        field in the request should be ``projects/_/buckets/{bucket}``.

        Returns:
            Callable[[~.GetIamPolicyRequest],
                    Awaitable[~.Policy]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_iam_policy' not in self._stubs:
            self._stubs['get_iam_policy'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetIamPolicy',
                request_serializer=iam_policy_pb2.GetIamPolicyRequest.SerializeToString,
                response_deserializer=policy_pb2.Policy.FromString,
            )
        return self._stubs['get_iam_policy']

    @property
    def set_iam_policy(self) -> Callable[
            [iam_policy_pb2.SetIamPolicyRequest],
            Awaitable[policy_pb2.Policy]]:
        r"""Return a callable for the set iam policy method over gRPC.

        Updates an IAM policy for the specified bucket. The ``resource``
        field in the request should be ``projects/_/buckets/{bucket}``.

        Returns:
            Callable[[~.SetIamPolicyRequest],
                    Awaitable[~.Policy]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'set_iam_policy' not in self._stubs:
            self._stubs['set_iam_policy'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/SetIamPolicy',
                request_serializer=iam_policy_pb2.SetIamPolicyRequest.SerializeToString,
                response_deserializer=policy_pb2.Policy.FromString,
            )
        return self._stubs['set_iam_policy']

    @property
    def test_iam_permissions(self) -> Callable[
            [iam_policy_pb2.TestIamPermissionsRequest],
            Awaitable[iam_policy_pb2.TestIamPermissionsResponse]]:
        r"""Return a callable for the test iam permissions method over gRPC.

        Tests a set of permissions on the given bucket, object, or
        managed folder to see which, if any, are held by the caller. The
        ``resource`` field in the request should be
        ``projects/_/buckets/{bucket}`` for a bucket,
        ``projects/_/buckets/{bucket}/objects/{object}`` for an object,
        or
        ``projects/_/buckets/{bucket}/managedFolders/{managedFolder}``
        for a managed folder.

        Returns:
            Callable[[~.TestIamPermissionsRequest],
                    Awaitable[~.TestIamPermissionsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'test_iam_permissions' not in self._stubs:
            self._stubs['test_iam_permissions'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/TestIamPermissions',
                request_serializer=iam_policy_pb2.TestIamPermissionsRequest.SerializeToString,
                response_deserializer=iam_policy_pb2.TestIamPermissionsResponse.FromString,
            )
        return self._stubs['test_iam_permissions']

    @property
    def update_bucket(self) -> Callable[
            [storage.UpdateBucketRequest],
            Awaitable[storage.Bucket]]:
        r"""Return a callable for the update bucket method over gRPC.

        Updates a bucket. Equivalent to JSON API's
        storage.buckets.patch method.

        Returns:
            Callable[[~.UpdateBucketRequest],
                    Awaitable[~.Bucket]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'update_bucket' not in self._stubs:
            self._stubs['update_bucket'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/UpdateBucket',
                request_serializer=storage.UpdateBucketRequest.serialize,
                response_deserializer=storage.Bucket.deserialize,
            )
        return self._stubs['update_bucket']

    @property
    def compose_object(self) -> Callable[
            [storage.ComposeObjectRequest],
            Awaitable[storage.Object]]:
        r"""Return a callable for the compose object method over gRPC.

        Concatenates a list of existing objects into a new
        object in the same bucket.

        Returns:
            Callable[[~.ComposeObjectRequest],
                    Awaitable[~.Object]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'compose_object' not in self._stubs:
            self._stubs['compose_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ComposeObject',
                request_serializer=storage.ComposeObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['compose_object']

    @property
    def delete_object(self) -> Callable[
            [storage.DeleteObjectRequest],
            Awaitable[empty_pb2.Empty]]:
        r"""Return a callable for the delete object method over gRPC.

        Deletes an object and its metadata. Deletions are permanent if
        versioning is not enabled for the bucket, or if the generation
        parameter is used, or if `soft
        delete <https://cloud.google.com/storage/docs/soft-delete>`__ is
        not enabled for the bucket. When this API is used to delete an
        object from a bucket that has soft delete policy enabled, the
        object becomes soft deleted, and the ``softDeleteTime`` and
        ``hardDeleteTime`` properties are set on the object. This API
        cannot be used to permanently delete soft-deleted objects.
        Soft-deleted objects are permanently deleted according to their
        ``hardDeleteTime``.

        You can use the
        [``RestoreObject``][google.storage.v2.Storage.RestoreObject] API
        to restore soft-deleted objects until the soft delete retention
        period has passed.

        **IAM Permissions**:

        Requires ``storage.objects.delete`` `IAM
        permission <https://cloud.google.com/iam/docs/overview#permissions>`__
        on the bucket.

        Returns:
            Callable[[~.DeleteObjectRequest],
                    Awaitable[~.Empty]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'delete_object' not in self._stubs:
            self._stubs['delete_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/DeleteObject',
                request_serializer=storage.DeleteObjectRequest.serialize,
                response_deserializer=empty_pb2.Empty.FromString,
            )
        return self._stubs['delete_object']

    @property
    def restore_object(self) -> Callable[
            [storage.RestoreObjectRequest],
            Awaitable[storage.Object]]:
        r"""Return a callable for the restore object method over gRPC.

        Restores a soft-deleted object.

        Returns:
            Callable[[~.RestoreObjectRequest],
                    Awaitable[~.Object]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'restore_object' not in self._stubs:
            self._stubs['restore_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/RestoreObject',
                request_serializer=storage.RestoreObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['restore_object']

    @property
    def cancel_resumable_write(self) -> Callable[
            [storage.CancelResumableWriteRequest],
            Awaitable[storage.CancelResumableWriteResponse]]:
        r"""Return a callable for the cancel resumable write method over gRPC.

        Cancels an in-progress resumable upload.

        Any attempts to write to the resumable upload after
        cancelling the upload will fail.

        The behavior for currently in progress write operations
        is not guaranteed - they could either complete before
        the cancellation or fail if the cancellation completes
        first.

        Returns:
            Callable[[~.CancelResumableWriteRequest],
                    Awaitable[~.CancelResumableWriteResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'cancel_resumable_write' not in self._stubs:
            self._stubs['cancel_resumable_write'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/CancelResumableWrite',
                request_serializer=storage.CancelResumableWriteRequest.serialize,
                response_deserializer=storage.CancelResumableWriteResponse.deserialize,
            )
        return self._stubs['cancel_resumable_write']

    @property
    def get_object(self) -> Callable[
            [storage.GetObjectRequest],
            Awaitable[storage.Object]]:
        r"""Return a callable for the get object method over gRPC.

        Retrieves object metadata.

        **IAM Permissions**:

        Requires ``storage.objects.get`` `IAM
        permission <https://cloud.google.com/iam/docs/overview#permissions>`__
        on the bucket. To return object ACLs, the authenticated user
        must also have the ``storage.objects.getIamPolicy`` permission.

        Returns:
            Callable[[~.GetObjectRequest],
                    Awaitable[~.Object]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'get_object' not in self._stubs:
            self._stubs['get_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/GetObject',
                request_serializer=storage.GetObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['get_object']

    @property
    def read_object(self) -> Callable[
            [storage.ReadObjectRequest],
            Awaitable[storage.ReadObjectResponse]]:
        r"""Return a callable for the read object method over gRPC.

        Retrieves object data.

        **IAM Permissions**:

        Requires ``storage.objects.get`` `IAM
        permission <https://cloud.google.com/iam/docs/overview#permissions>`__
        on the bucket.

        Returns:
            Callable[[~.ReadObjectRequest],
                    Awaitable[~.ReadObjectResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'read_object' not in self._stubs:
            self._stubs['read_object'] = self.grpc_channel.unary_stream(
                '/google.storage.v2.Storage/ReadObject',
                request_serializer=storage.ReadObjectRequest.serialize,
                response_deserializer=storage.ReadObjectResponse.deserialize,
            )
        return self._stubs['read_object']

    @property
    def update_object(self) -> Callable[
            [storage.UpdateObjectRequest],
            Awaitable[storage.Object]]:
        r"""Return a callable for the update object method over gRPC.

        Updates an object's metadata.
        Equivalent to JSON API's storage.objects.patch.

        Returns:
            Callable[[~.UpdateObjectRequest],
                    Awaitable[~.Object]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'update_object' not in self._stubs:
            self._stubs['update_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/UpdateObject',
                request_serializer=storage.UpdateObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['update_object']

    @property
    def write_object(self) -> Callable[
            [storage.WriteObjectRequest],
            Awaitable[storage.WriteObjectResponse]]:
        r"""Return a callable for the write object method over gRPC.

        Stores a new object and metadata.

        An object can be written either in a single message stream or in
        a resumable sequence of message streams. To write using a single
        stream, the client should include in the first message of the
        stream an ``WriteObjectSpec`` describing the destination bucket,
        object, and any preconditions. Additionally, the final message
        must set 'finish_write' to true, or else it is an error.

        For a resumable write, the client should instead call
        ``StartResumableWrite()``, populating a ``WriteObjectSpec`` into
        that request. They should then attach the returned ``upload_id``
        to the first message of each following call to ``WriteObject``.
        If the stream is closed before finishing the upload (either
        explicitly by the client or due to a network error or an error
        response from the server), the client should do as follows:

        -  Check the result Status of the stream, to determine if
           writing can be resumed on this stream or must be restarted
           from scratch (by calling ``StartResumableWrite()``). The
           resumable errors are DEADLINE_EXCEEDED, INTERNAL, and
           UNAVAILABLE. For each case, the client should use binary
           exponential backoff before retrying. Additionally, writes can
           be resumed after RESOURCE_EXHAUSTED errors, but only after
           taking appropriate measures, which may include reducing
           aggregate send rate across clients and/or requesting a quota
           increase for your project.
        -  If the call to ``WriteObject`` returns ``ABORTED``, that
           indicates concurrent attempts to update the resumable write,
           caused either by multiple racing clients or by a single
           client where the previous request was timed out on the client
           side but nonetheless reached the server. In this case the
           client should take steps to prevent further concurrent writes
           (e.g., increase the timeouts, stop using more than one
           process to perform the upload, etc.), and then should follow
           the steps below for resuming the upload.
        -  For resumable errors, the client should call
           ``QueryWriteStatus()`` and then continue writing from the
           returned ``persisted_size``. This may be less than the amount
           of data the client previously sent. Note also that it is
           acceptable to send data starting at an offset earlier than
           the returned ``persisted_size``; in this case, the service
           will skip data at offsets that were already persisted
           (without checking that it matches the previously written
           data), and write only the data starting from the persisted
           offset. Even though the data isn't written, it may still
           incur a performance cost over resuming at the correct write
           offset. This behavior can make client-side handling simpler
           in some cases.
        -  Clients must only send data that is a multiple of 256 KiB per
           message, unless the object is being finished with
           ``finish_write`` set to ``true``.

        The service will not view the object as complete until the
        client has sent a ``WriteObjectRequest`` with ``finish_write``
        set to ``true``. Sending any requests on a stream after sending
        a request with ``finish_write`` set to ``true`` will cause an
        error. The client **should** check the response it receives to
        determine how much data the service was able to commit and
        whether the service views the object as complete.

        Attempting to resume an already finalized object will result in
        an OK status, with a ``WriteObjectResponse`` containing the
        finalized object's metadata.

        Alternatively, the BidiWriteObject operation may be used to
        write an object with controls over flushing and the ability to
        fetch the ability to determine the current persisted size.

        **IAM Permissions**:

        Requires ``storage.objects.create`` `IAM
        permission <https://cloud.google.com/iam/docs/overview#permissions>`__
        on the bucket.

        Returns:
            Callable[[~.WriteObjectRequest],
                    Awaitable[~.WriteObjectResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'write_object' not in self._stubs:
            self._stubs['write_object'] = self.grpc_channel.stream_unary(
                '/google.storage.v2.Storage/WriteObject',
                request_serializer=storage.WriteObjectRequest.serialize,
                response_deserializer=storage.WriteObjectResponse.deserialize,
            )
        return self._stubs['write_object']

    @property
    def bidi_write_object(self) -> Callable[
            [storage.BidiWriteObjectRequest],
            Awaitable[storage.BidiWriteObjectResponse]]:
        r"""Return a callable for the bidi write object method over gRPC.

        Stores a new object and metadata.

        This is similar to the WriteObject call with the added support
        for manual flushing of persisted state, and the ability to
        determine current persisted size without closing the stream.

        The client may specify one or both of the ``state_lookup`` and
        ``flush`` fields in each BidiWriteObjectRequest. If ``flush`` is
        specified, the data written so far will be persisted to storage.
        If ``state_lookup`` is specified, the service will respond with
        a BidiWriteObjectResponse that contains the persisted size. If
        both ``flush`` and ``state_lookup`` are specified, the flush
        will always occur before a ``state_lookup``, so that both may be
        set in the same request and the returned state will be the state
        of the object post-flush. When the stream is closed, a
        BidiWriteObjectResponse will always be sent to the client,
        regardless of the value of ``state_lookup``.

        Returns:
            Callable[[~.BidiWriteObjectRequest],
                    Awaitable[~.BidiWriteObjectResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'bidi_write_object' not in self._stubs:
            self._stubs['bidi_write_object'] = self.grpc_channel.stream_stream(
                '/google.storage.v2.Storage/BidiWriteObject',
                request_serializer=storage.BidiWriteObjectRequest.serialize,
                response_deserializer=storage.BidiWriteObjectResponse.deserialize,
            )
        return self._stubs['bidi_write_object']

    @property
    def list_objects(self) -> Callable[
            [storage.ListObjectsRequest],
            Awaitable[storage.ListObjectsResponse]]:
        r"""Return a callable for the list objects method over gRPC.

        Retrieves a list of objects matching the criteria.

        **IAM Permissions**:

        The authenticated user requires ``storage.objects.list`` `IAM
        permission <https://cloud.google.com/iam/docs/overview#permissions>`__
        to use this method. To return object ACLs, the authenticated
        user must also have the ``storage.objects.getIamPolicy``
        permission.

        Returns:
            Callable[[~.ListObjectsRequest],
                    Awaitable[~.ListObjectsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'list_objects' not in self._stubs:
            self._stubs['list_objects'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/ListObjects',
                request_serializer=storage.ListObjectsRequest.serialize,
                response_deserializer=storage.ListObjectsResponse.deserialize,
            )
        return self._stubs['list_objects']

    @property
    def rewrite_object(self) -> Callable[
            [storage.RewriteObjectRequest],
            Awaitable[storage.RewriteResponse]]:
        r"""Return a callable for the rewrite object method over gRPC.

        Rewrites a source object to a destination object.
        Optionally overrides metadata.

        Returns:
            Callable[[~.RewriteObjectRequest],
                    Awaitable[~.RewriteResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'rewrite_object' not in self._stubs:
            self._stubs['rewrite_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/RewriteObject',
                request_serializer=storage.RewriteObjectRequest.serialize,
                response_deserializer=storage.RewriteResponse.deserialize,
            )
        return self._stubs['rewrite_object']

    @property
    def start_resumable_write(self) -> Callable[
            [storage.StartResumableWriteRequest],
            Awaitable[storage.StartResumableWriteResponse]]:
        r"""Return a callable for the start resumable write method over gRPC.

        Starts a resumable write operation. This method is part of the
        `Resumable
        upload <https://cloud.google.com/storage/docs/resumable-uploads>`__
        feature. This allows you to upload large objects in multiple
        chunks, which is more resilient to network interruptions than a
        single upload. The validity duration of the write operation, and
        the consequences of it becoming invalid, are service-dependent.

        **IAM Permissions**:

        Requires ``storage.objects.create`` `IAM
        permission <https://cloud.google.com/iam/docs/overview#permissions>`__
        on the bucket.

        Returns:
            Callable[[~.StartResumableWriteRequest],
                    Awaitable[~.StartResumableWriteResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'start_resumable_write' not in self._stubs:
            self._stubs['start_resumable_write'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/StartResumableWrite',
                request_serializer=storage.StartResumableWriteRequest.serialize,
                response_deserializer=storage.StartResumableWriteResponse.deserialize,
            )
        return self._stubs['start_resumable_write']

    @property
    def query_write_status(self) -> Callable[
            [storage.QueryWriteStatusRequest],
            Awaitable[storage.QueryWriteStatusResponse]]:
        r"""Return a callable for the query write status method over gRPC.

        Determines the ``persisted_size`` of an object that is being
        written. This method is part of the `resumable
        upload <https://cloud.google.com/storage/docs/resumable-uploads>`__
        feature. The returned value is the size of the object that has
        been persisted so far. The value can be used as the
        ``write_offset`` for the next ``Write()`` call.

        If the object does not exist, meaning if it was deleted, or the
        first ``Write()`` has not yet reached the service, this method
        returns the error ``NOT_FOUND``.

        This method is useful for clients that buffer data and need to
        know which data can be safely evicted. The client can call
        ``QueryWriteStatus()`` at any time to determine how much data
        has been logged for this object. For any sequence of
        ``QueryWriteStatus()`` calls for a given object name, the
        sequence of returned ``persisted_size`` values are
        non-decreasing.

        Returns:
            Callable[[~.QueryWriteStatusRequest],
                    Awaitable[~.QueryWriteStatusResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'query_write_status' not in self._stubs:
            self._stubs['query_write_status'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/QueryWriteStatus',
                request_serializer=storage.QueryWriteStatusRequest.serialize,
                response_deserializer=storage.QueryWriteStatusResponse.deserialize,
            )
        return self._stubs['query_write_status']

    @property
    def move_object(self) -> Callable[
            [storage.MoveObjectRequest],
            Awaitable[storage.Object]]:
        r"""Return a callable for the move object method over gRPC.

        Moves the source object to the destination object in
        the same bucket.

        Returns:
            Callable[[~.MoveObjectRequest],
                    Awaitable[~.Object]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if 'move_object' not in self._stubs:
            self._stubs['move_object'] = self.grpc_channel.unary_unary(
                '/google.storage.v2.Storage/MoveObject',
                request_serializer=storage.MoveObjectRequest.serialize,
                response_deserializer=storage.Object.deserialize,
            )
        return self._stubs['move_object']

    def _prep_wrapped_messages(self, client_info):
        """ Precompute the wrapped methods, overriding the base class method to use async wrappers."""
        self._wrapped_methods = {
            self.delete_bucket: gapic_v1.method_async.wrap_method(
                self.delete_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_bucket: gapic_v1.method_async.wrap_method(
                self.get_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.create_bucket: gapic_v1.method_async.wrap_method(
                self.create_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.list_buckets: gapic_v1.method_async.wrap_method(
                self.list_buckets,
                default_timeout=None,
                client_info=client_info,
            ),
            self.lock_bucket_retention_policy: gapic_v1.method_async.wrap_method(
                self.lock_bucket_retention_policy,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_iam_policy: gapic_v1.method_async.wrap_method(
                self.get_iam_policy,
                default_timeout=None,
                client_info=client_info,
            ),
            self.set_iam_policy: gapic_v1.method_async.wrap_method(
                self.set_iam_policy,
                default_timeout=None,
                client_info=client_info,
            ),
            self.test_iam_permissions: gapic_v1.method_async.wrap_method(
                self.test_iam_permissions,
                default_timeout=None,
                client_info=client_info,
            ),
            self.update_bucket: gapic_v1.method_async.wrap_method(
                self.update_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.compose_object: gapic_v1.method_async.wrap_method(
                self.compose_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.delete_object: gapic_v1.method_async.wrap_method(
                self.delete_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.restore_object: gapic_v1.method_async.wrap_method(
                self.restore_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.cancel_resumable_write: gapic_v1.method_async.wrap_method(
                self.cancel_resumable_write,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_object: gapic_v1.method_async.wrap_method(
                self.get_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.read_object: gapic_v1.method_async.wrap_method(
                self.read_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.update_object: gapic_v1.method_async.wrap_method(
                self.update_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.write_object: gapic_v1.method_async.wrap_method(
                self.write_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.bidi_write_object: gapic_v1.method_async.wrap_method(
                self.bidi_write_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.list_objects: gapic_v1.method_async.wrap_method(
                self.list_objects,
                default_timeout=None,
                client_info=client_info,
            ),
            self.rewrite_object: gapic_v1.method_async.wrap_method(
                self.rewrite_object,
                default_timeout=None,
                client_info=client_info,
            ),
            self.start_resumable_write: gapic_v1.method_async.wrap_method(
                self.start_resumable_write,
                default_timeout=None,
                client_info=client_info,
            ),
            self.query_write_status: gapic_v1.method_async.wrap_method(
                self.query_write_status,
                default_timeout=None,
                client_info=client_info,
            ),
            self.move_object: gapic_v1.method_async.wrap_method(
                self.move_object,
                default_timeout=None,
                client_info=client_info,
            ),
         }

    def close(self):
        return self.grpc_channel.close()


__all__ = (
    'StorageGrpcAsyncIOTransport',
)