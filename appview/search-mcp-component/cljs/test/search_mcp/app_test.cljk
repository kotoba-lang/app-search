(ns search-mcp.app-test
  (:require [cljs.test :refer [deftest is testing use-fixtures]]
            [re-frame.core :as rf]
            [re-frame.db :as rf-db]
            [search-mcp.app :as app]))

;; re-frame keeps its db in a global atom (re-frame.db/app-db). Reset it
;; around each test so events fired in one test can't leak into the next.
(use-fixtures :each
  {:before (fn [] (reset! rf-db/app-db {}))})

(deftest initialize-sets-defaults
  (testing "::initialize seeds the ported Svelte scaffold's title/subtitle"
    (rf/dispatch-sync [::app/initialize])
    (is (= "search-mcp-component" @(rf/subscribe [::app/title])))
    (is (= "Vite entry scaffold after SvelteKit cleanup."
           @(rf/subscribe [::app/subtitle])))))

(deftest initial-db-matches-subs
  (testing "initial-db is the single source the subs read from"
    (is (= "search-mcp-component" (:title app/initial-db)))
    (is (= "Vite entry scaffold after SvelteKit cleanup." (:subtitle app/initial-db)))))

(deftest app-view-renders-hiccup
  (testing "app-view returns a hiccup vector rooted at :main, wrapping the DADS container"
    (rf/dispatch-sync [::app/initialize])
    (let [hiccup (app/app-view)]
      (is (vector? hiccup))
      (is (= :main (first hiccup)))
      (let [container (second hiccup)]
        (is (vector? container))
        (is (= :div (first container)))
        (is (= "dds-ext-container" (:class (second container))))))))
