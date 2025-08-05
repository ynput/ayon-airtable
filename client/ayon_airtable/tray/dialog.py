"""Dialog and tray menu integration for the AYON Airtable Addon.

This module provides a Qt dialog for validating Airtable API settings and
integrates with the AYON tray menu to display Airtable connection status.
"""

import requests
from ayon_core.addon import AYONAddon
from qtpy import QtWidgets

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404


class AirtableTrayDialog(QtWidgets.QDialog):
    """Tray UI for AYON Airtable Addon."""

    def __init__(
        self,
        addon: AYONAddon,
        parent: QtWidgets.QWidget = None,
    ) -> None:
        """Initialize the AirtableTrayDialog."""
        super().__init__(parent)
        self.addon = addon

        self.setWindowTitle("Validate Airtable Tray")
        # add validate function to ensure the settings applied to the airtable
        api_key = self.addon.get_api_secret()
        # use requests to check if the Airtable API is reachable
        validate = self.validate_settings(api_key)
        if validate:
            self.host_action = QtWidgets.QAction("Airtable API Key: Valid")
        else:
            self.host_action = QtWidgets.QAction("Airtable API Key: Invalid")

        self.host_action.setDisabled(True)

    def tray_menu(self, tray_menu: QtWidgets.QMenu) -> None:
        """Add Airtable Submenu to AYON tray.

        A non-actionable action displays the Airtable URL and the other
        action allows the user to set and check their Airtable username.

        Args:
            tray_menu (QtWidgets.QMenu): The AYON Tray menu.
        """
        airtable_tray_menu = QtWidgets.QMenu("Airtable", tray_menu)
        airtable_tray_menu.addAction(self.host_action)
        airtable_tray_menu.addSeparator()
        tray_menu.addMenu(airtable_tray_menu)

    def validate_settings(self, api_key: str) -> bool:
        """Validate the Airtable settings by making a real API call.

        Args:
            api_key (str): The Airtable API key to validate.

        Returns:
            bool: True if the Airtable API is reachable and the key is valid,
            False otherwise.

        Raises:
            RuntimeError: If the Airtable API is unreachable or the API key is
            invalid.
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            "https://api.airtable.com", headers=headers, timeout=10)
        try:
            if response.status_code == HTTP_OK:
                self.log.info("Airtable API is reachable.")

            elif response.status_code == HTTP_UNAUTHORIZED:
                msg = (
                    "Airtable Authentication Failed. Invalid Airtable API Key "
                    "(token). Please check your settings."
                )
                raise RuntimeError(msg)

            else:
                msg = (
                    f"Airtable API returned status code "
                    f"{response.status_code}: {response.text}"
                )
                raise RuntimeError(msg)

        except requests.RequestException as e:
            msg = f"Could not connect to Airtable API: {e}"
            raise RuntimeError(msg) from e

        return response.status_code == HTTP_OK
