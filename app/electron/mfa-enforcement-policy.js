// Attached as an inline user policy alongside AdministratorAccess on every IAM
// user created via create-iam-user. IAM policy evaluation gives explicit Deny
// statements priority over Allow (including managed-policy Allows like
// AdministratorAccess), so this turns "admin" into "admin only when
// authenticated with MFA" while still permitting the handful of self-service
// actions the user needs to enroll/maintain their own MFA device and mint a
// session — otherwise they could never bootstrap their first device.
//
// BoolIfExists (not Bool) matters: aws:MultiFactorAuthPresent only exists as
// a context key on requests using temporary (STS) credentials. A raw call
// using the IAM user's permanent access key has no such key at all, and a
// plain Bool condition doesn't match a missing key — which would mean the
// Deny never fires for permanent-key requests. BoolIfExists treats a missing
// key as "false", correctly denying both cases.
const mfaEnforcementPolicy = {
  Version: '2012-10-17',
  Statement: [
    {
      Sid: 'AllowReadOnlyStatusChecksWithoutMFA',
      Effect: 'Allow',
      Action: ['iam:GetAccountSummary', 'iam:ListVirtualMFADevices', 'sts:GetCallerIdentity', 'ec2:DescribeInstances'],
      Resource: '*',
    },
    {
      Sid: 'AllowManageOwnVirtualMFADeviceWithoutMFA',
      Effect: 'Allow',
      Action: ['iam:CreateVirtualMFADevice', 'iam:DeleteVirtualMFADevice'],
      Resource: 'arn:aws:iam::*:mfa/${aws:username}',
    },
    {
      Sid: 'AllowManageOwnUserMFAWithoutMFA',
      Effect: 'Allow',
      Action: ['iam:EnableMFADevice', 'iam:DeactivateMFADevice', 'iam:ListMFADevices', 'iam:ResyncMFADevice'],
      Resource: 'arn:aws:iam::*:user/${aws:username}',
    },
    {
      Sid: 'AllowGetSessionTokenWithoutMFA',
      Effect: 'Allow',
      Action: 'sts:GetSessionToken',
      Resource: '*',
      Condition: { NumericLessThanEquals: { 'sts:DurationSeconds': '14400' } },
    },
    {
      Sid: 'DenyEverythingElseUnlessMFAPresent',
      Effect: 'Deny',
      NotAction: [
        'iam:GetAccountSummary',
        'iam:ListVirtualMFADevices',
        'sts:GetCallerIdentity',
        'ec2:DescribeInstances',
        'iam:CreateVirtualMFADevice',
        'iam:DeleteVirtualMFADevice',
        'iam:EnableMFADevice',
        'iam:DeactivateMFADevice',
        'iam:ListMFADevices',
        'iam:ResyncMFADevice',
        'sts:GetSessionToken',
      ],
      Resource: '*',
      Condition: { BoolIfExists: { 'aws:MultiFactorAuthPresent': 'false' } },
    },
  ],
}

module.exports = { mfaEnforcementPolicy }
