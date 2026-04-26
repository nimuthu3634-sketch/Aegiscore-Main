import { QRCodeSVG } from "qrcode.react";
import { useCallback, useState } from "react";
import { Modal } from "../../components/feedback/Modal";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import {
  ApiRequestError,
  disableMfa,
  fetchMfaSetup,
  type MfaSetupPayload,
  verifyMfaSetup
} from "../../lib/api";

type MfaSetupModalProps = {
  open: boolean;
  onClose: () => void;
  mfaEnabled: boolean;
  isAdmin: boolean;
  onProfileChanged: () => void;
};

export function MfaSetupModal({
  open,
  onClose,
  mfaEnabled,
  isAdmin,
  onProfileChanged
}: MfaSetupModalProps) {
  const [setupPayload, setSetupPayload] = useState<MfaSetupPayload | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const resetLocal = useCallback(() => {
    setSetupPayload(null);
    setCode("");
    setError(null);
    setBusy(false);
  }, []);

  const handleClose = () => {
    resetLocal();
    onClose();
  };

  const handleStartSetup = async () => {
    setError(null);
    setBusy(true);
    try {
      const data = await fetchMfaSetup();
      setSetupPayload(data);
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.message : "Could not start MFA setup."
      );
    } finally {
      setBusy(false);
    }
  };

  const handleConfirmSetup = async () => {
    if (!code.trim() || code.trim().length !== 6) {
      setError("Enter the 6-digit code from your authenticator app.");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      await verifyMfaSetup(code);
      resetLocal();
      onProfileChanged();
      onClose();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.message : "Verification failed."
      );
    } finally {
      setBusy(false);
    }
  };

  const handleDisable = async () => {
    setError(null);
    setBusy(true);
    try {
      await disableMfa();
      resetLocal();
      onProfileChanged();
      onClose();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.message : "Could not disable MFA."
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Authenticator (TOTP)"
      description="Set up Google Authenticator–compatible MFA for this operator account."
      size="md"
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="type-label-sm text-content-muted">MFA status</span>
          <span
            className={
              mfaEnabled
                ? "rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-body-sm font-medium text-emerald-400"
                : "rounded-full bg-amber-500/15 px-2.5 py-0.5 text-body-sm font-medium text-amber-400"
            }
          >
            {mfaEnabled ? "Enabled" : "Not enabled"}
          </span>
        </div>

        {mfaEnabled ? (
          <div className="space-y-4">
            <p className="type-body-sm text-content-secondary">
              This account is protected with a time-based one-time password. Use your
              authenticator app when signing in.
            </p>
            {isAdmin ? (
              <div className="space-y-2">
                <p className="type-body-sm text-content-muted">
                  Admins can disable MFA for their own account if a device is lost.
                </p>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void handleDisable()}
                  disabled={busy}
                >
                  {busy ? "Working…" : "Disable MFA"}
                </Button>
              </div>
            ) : (
              <p className="type-body-sm text-content-muted">
                Contact an administrator if you need MFA reset on this account.
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {!setupPayload ? (
              <Button
                type="button"
                variant="primary"
                onClick={() => void handleStartSetup()}
                disabled={busy}
              >
                {busy ? "Generating…" : "Generate QR code & secret"}
              </Button>
            ) : (
              <>
                <p className="type-body-sm text-content-secondary">
                  Scan the QR code or enter the secret manually, then enter a 6-digit code
                  to confirm.
                </p>
                <div className="flex flex-col items-center gap-4 rounded-field border border-border-subtle bg-surface-subtle/40 p-4 sm:flex-row sm:items-start">
                  <div className="rounded-md bg-white p-2">
                    <QRCodeSVG value={setupPayload.provisioning_uri} size={160} level="M" />
                  </div>
                  <div className="min-w-0 flex-1 space-y-2">
                    <p className="type-label-sm text-content-muted">Secret (base32)</p>
                    <code className="block break-all rounded border border-border-subtle bg-[#0A0A0A] px-3 py-2 text-body-sm text-content-primary">
                      {setupPayload.secret}
                    </code>
                  </div>
                </div>
                <Input
                  label="Confirmation code"
                  value={code}
                  onChange={(e) => {
                    const v = e.target.value.replace(/\D/g, "").slice(0, 6);
                    setCode(v);
                    if (error) {
                      setError(null);
                    }
                  }}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  placeholder="000000"
                  maxLength={6}
                />
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="primary"
                    onClick={() => void handleConfirmSetup()}
                    disabled={busy || code.length !== 6}
                  >
                    {busy ? "Verifying…" : "Enable MFA"}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      setSetupPayload(null);
                      setCode("");
                      setError(null);
                    }}
                    disabled={busy}
                  >
                    Start over
                  </Button>
                </div>
              </>
            )}
          </div>
        )}

        {error ? <p className="text-body-sm text-status-danger">{error}</p> : null}
      </div>
    </Modal>
  );
}
