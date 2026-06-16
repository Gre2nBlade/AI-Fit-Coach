// Производные метрики (зеркало backend/services/user_service.compute_metrics).
// Нужны, чтобы показывать калории/КБЖУ/BMI мгновенно, не дожидаясь сервера.

const ACTIVITY = { 0: 1.2, 1: 1.3, 2: 1.4, 3: 1.5, 4: 1.6, 5: 1.7, 6: 1.8, 7: 1.9 };

function computeMetrics(p) {
  const age = Number(p.age);
  const height = Number(p.height_cm ?? p.height);
  const weight = Number(p.weight_kg ?? p.weight);
  const sex = (p.sex || "").toLowerCase();
  if (!age || !height || !weight || !sex) return null;

  const isMale = sex.startsWith("м") || sex.startsWith("m");
  const bmr = 10 * weight + 6.25 * height - 5 * age + (isMale ? 5 : -161);

  const daysStr = p.training_days || (Array.isArray(p.days) ? p.days.join(",") : "");
  const days = daysStr.split(",").filter((d) => d.trim()).length;
  const tdee = bmr * (ACTIVITY[days] || 1.4);

  const goal = (p.goal || "").toLowerCase();
  let calories = tdee;
  if (goal.includes("похуд")) calories = tdee - 400;
  else if (goal.includes("набор") || goal.includes("масс")) calories = tdee + 350;
  calories = Math.round(calories);

  const protein_g = Math.round(weight * 2);
  const fat_g = Math.round(weight * 1);
  const carbs_g = Math.max(0, Math.round((calories - protein_g * 4 - fat_g * 9) / 4));
  const bmi = Math.round((weight / Math.pow(height / 100, 2)) * 10) / 10;
  const water_l = Math.round(weight * 0.033 * 10) / 10;

  return { bmr: Math.round(bmr), tdee: Math.round(tdee), calories,
           protein_g, fat_g, carbs_g, bmi, water_l, training_days_count: days };
}
