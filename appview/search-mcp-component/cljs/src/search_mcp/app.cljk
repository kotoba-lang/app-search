(ns search-mcp.app
  "search-mcp-component — reagent + re-frame port of the former Svelte
  frontend at appview/search-mcp-component/svelte/src/.

  There was exactly one Svelte component (`App.svelte`, a centered heading +
  message: \"Vite entry scaffold after SvelteKit cleanup.\") mounted directly
  by `main.ts` via plain Vite's `mount(App, {target: ...})` — this was a bare
  Vite + Svelte entry, not SvelteKit (`vite.config.ts` had no SvelteKit
  plugin), so there is no separate route layer to account for. `app-view` is
  a faithful port of that single component's markup, and `main` (mounted at
  document load) is the equivalent of the original `main.ts` entry. There was
  only ever one screen, so a single `app-view` mounted once is a faithful
  port, not a simplification (ADR-2608080100: one document, one bundle, one
  mount)."
  (:require [reagent.dom :as rdom]
            [re-frame.core :as rf]
            [jp-go-dds.core :as dds]))

;; --- db --------------------------------------------------------------------

(def initial-db
  {:title "search-mcp-component"
   :subtitle "Vite entry scaffold after SvelteKit cleanup."})

(rf/reg-event-db
 ::initialize
 (fn [_ _] initial-db))

(rf/reg-sub ::title (fn [db _] (:title db)))
(rf/reg-sub ::subtitle (fn [db _] (:subtitle db)))

;; --- view --------------------------------------------------------------------
;;
;; Faithful port of App.svelte: a full-viewport centered column with a
;; heading and a paragraph message (the Svelte version used
;; `min-height: 100vh; display: grid; place-content: center` on `main`;
;; `dds-ext-hero dds-ext-center` gives the same centered-column composition
;; through jp-go-dds's layout extension classes instead of hand-rolled CSS).

(defn app-view []
  (let [title @(rf/subscribe [::title])
        subtitle @(rf/subscribe [::subtitle])]
    [:main
     (dds/container
      (dds/section {}
        [:div {:class "dds-ext-hero dds-ext-center"}
         (dds/heading 1 title)
         [:p {:class "dds-ext-lead"} subtitle]]))]))

(defn ^:dev/after-load render! []
  (rdom/render [app-view] (.getElementById js/document "app")))

(defn ^:export main []
  (rf/dispatch-sync [::initialize])
  (render!))
