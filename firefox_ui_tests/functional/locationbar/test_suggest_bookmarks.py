# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette_driver import By

from firefox_ui_harness.decorators import skip_under_xvfb
from firefox_ui_harness import FirefoxTestCase


@skip_under_xvfb
class TestStarInAutocomplete(FirefoxTestCase):
    """ This replaces
    http://hg.mozilla.org/qa/mozmill-tests/file/default/firefox/tests/functional/testAwesomeBar/testSuggestBookmarks.js
    Check a star appears in autocomplete list for a bookmarked page.
    """

    PREF_LOCATION_BAR_SUGGEST = 'browser.urlbar.default.behavior'

    def setUp(self):
        FirefoxTestCase.setUp(self)

        self.test_urls = [self.marionette.absolute_url('layout/mozilla_grants.html')]

        # Location bar suggests 'History and Bookmarks'
        self.prefs.set_pref(self.PREF_LOCATION_BAR_SUGGEST, 0)

        with self.marionette.using_context('content'):
            self.marionette.navigate('about:blank')

        self.places.remove_all_history()

    def tearDown(self):
        # Close the autocomplete results
        try:
            self.browser.navbar.locationbar.autocomplete_results.close()
            self.places.restore_default_bookmarks()
        finally:
            FirefoxTestCase.tearDown(self)

    def test_star_in_autocomplete(self):
        search_string = 'grants'

        def visit_urls():
            with self.marionette.using_context('content'):
                for url in self.test_urls:
                    self.marionette.navigate(url)

        # Navigate to all the urls specified in self.test_urls and wait for them to
        # be registered as visited
        self.places.wait_for_visited(self.test_urls, visit_urls)

        # Bookmark the current page using the bookmark menu
        # TODO: Convert to l10n friendly accessor when menu library is available
        self.browser.menubar.select('Bookmarks', 'Bookmark This Page')
        # TODO: Replace hard-coded selector with library method when one is available
        done_button = self.marionette.find_element(By.ID, 'editBookmarkPanelDoneButton')
        self.wait_for_condition(lambda mn: done_button.is_displayed)
        done_button.click()

        # We must open the blank page so the autocomplete result isn't "Switch to tab"
        with self.marionette.using_context('content'):
            self.marionette.navigate('about:blank')

        self.places.remove_all_history()

        # Focus the locationbar, delete any contents there, and type the search string
        locationbar = self.browser.navbar.locationbar
        locationbar.clear()
        locationbar.urlbar.send_keys(search_string)
        autocomplete_results = locationbar.autocomplete_results

        # Wait for the search string to be present, for the autocomplete results to appear
        # and for there to be exactly one autocomplete result
        self.wait_for_condition(lambda mn: locationbar.value == search_string)
        self.wait_for_condition(lambda mn: autocomplete_results.is_open)
        self.wait_for_condition(lambda mn: len(autocomplete_results.visible_results) == 1)

        # Compare the highlighted text in the autocomplete result to the search string
        first_result = autocomplete_results.visible_results[0]
        matching_titles = autocomplete_results.get_matching_text(first_result, 'title')
        for title in matching_titles:
            self.wait_for_condition(lambda mn: title.lower() == search_string)

        self.assertIn('bookmark',
                      first_result.get_attribute('type'),
                      'The auto-complete result is a bookmark')
