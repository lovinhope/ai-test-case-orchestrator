(function () {
  "use strict";

  function installBridge() {
    if (window.__TEST_REVIEW_BRIDGE__) return;
    window.__TEST_REVIEW_BRIDGE__ = {
      submit: function (payload) {
        return fetch("/api/reviews/challenge/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Review-Stage": payload.stage, "X-CSRF-Token": window.__REVIEW_MODEL__.csrf_token },
          body: JSON.stringify(payload)
        }).then(function (response) {
          return response.json().then(function (body) {
            if (!response.ok || !body.accepted) throw new Error(body.error || "提交失败");
            return body;
          });
        });
      }
    };
  }

  function mount() {
    var model = window.__REVIEW_MODEL__;
    var root = document.getElementById("review-app");
    var unavailable = document.getElementById("vue-unavailable");
    if (!root || !model || !window.Vue) return;
    installBridge();
    var Vue = window.Vue;
    var app = Vue.createApp({
      data: function () {
        return {
          vueReady: true,
          reviewer: model.reviewer || "",
          items: model.questions.map(function (question) {
            return { id: question.id, number: question.number, title: question.title, response: "", reason: "", decision: "" };
          }),
          errors: {},
          formError: "",
          successMessage: "",
          submitting: false
        };
      },
      mounted: function () {
        unavailable.hidden = true;
      },
      methods: {
        validate: function () {
          var errors = {};
          if (!this.reviewer) this.formError = "请填写评审人";
          this.items.forEach(function (item) {
            if (!item.decision) errors[item.id] = "请选择确认规则、废弃问题或与本次测试无关";
            else if (item.decision === "confirmed" && !item.response) errors[item.id] = "确认规则时必须填写具体规则";
            else if (item.decision !== "confirmed" && !item.response && !item.reason) errors[item.id] = "请填写废弃或不相关的说明";
          });
          this.errors = errors;
          return !this.formError && Object.keys(errors).length === 0;
        },
        submitReview: async function () {
          this.formError = "";
          this.successMessage = "";
          if (!this.validate()) return;
          this.submitting = true;
          var payload = {
            run_id: model.run_id,
            stage: model.stage,
            case_id: model.case_id,
            artifact_path: model.artifact_path,
            reviewer: this.reviewer,
            submitted_at: new Date().toISOString(),
            items: this.items.map(function (item) {
              return { id: item.id, number: item.number, title: item.title, response: item.response, reason: item.reason, decision: item.decision };
            })
          };
          try {
            var result = await window.__TEST_REVIEW_BRIDGE__.submit(payload);
            if (!result.accepted || !result.persisted_artifact || !result.next_stage) throw new Error("宿主未确认持久化和阶段流转");
            this.successMessage = "评审已保存，将进入：" + result.next_stage;
          } catch (error) {
            this.formError = error.message || "提交失败，请稍后重试";
          } finally {
            this.submitting = false;
          }
        }
      }
    });
    app.mount("#review-app");
  }

  document.addEventListener("DOMContentLoaded", function () { setTimeout(mount, 0); });
}());
