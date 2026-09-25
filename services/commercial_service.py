"""
Commercial service layer.

This module models an authorized PSP/RSP workflow. It intentionally does not
store or process an end customer's IRCTC personal password, CAPTCHA, OTP,
session cookie, or payment credentials.

The exact agent charges, taxes, refund rules, branding and booking workflow
must be populated from the current IRCTC/PSP agreement and applicable rules.
"""


class CommercialBookingService:
    def __init__(self, railway_provider):
        self.railway_provider = railway_provider

    def quote(self, booking):
        # Do not invent IRCTC fees. The authorized provider/PSP should supply
        # the applicable fare and permitted service charges.
        return {
            "status": "requires_authorized_provider_quote",
            "message": "Fare/service charges must come from the authorized PSP/RSP configuration."
        }

    def search(self, source, destination, journey_date, quota="Tatkal"):
        return self.railway_provider.search_trains(
            source, destination, journey_date, quota
        )

    def pnr_status(self, pnr):
        return self.railway_provider.get_pnr_status(pnr)
