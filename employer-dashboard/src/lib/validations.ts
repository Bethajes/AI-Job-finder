import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Invalid email"),
  password: z.string().min(6, "Password too short"),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  first_name: z.string().min(1, "First name is required").max(100),
  last_name: z.string().min(1, "Last name is required").max(100),
  email: z.string().email("Invalid email"),
  phone: z
    .string()
    .max(20, "Phone too long")
    .optional()
    .or(z.literal("")),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
export type RegisterFormValues = z.infer<typeof registerSchema>;

const employmentTypes = [
  "full-time",
  "part-time",
  "contract",
  "internship",
  "remote",
] as const;

const experienceLevels = ["entry", "mid", "senior", "lead"] as const;

export const jobSchema = z
  .object({
    title: z
      .string()
      .min(3, "Title must be at least 3 characters")
      .max(200, "Title must be at most 200 characters"),
    description: z.string().min(10, "Description must be at least 10 characters"),
    requirements: z.string().optional().default(""),
    responsibilities: z.string().optional().default(""),
    employment_type: z.enum(employmentTypes),
    experience_level: z.enum(experienceLevels),
    salary_min: z
      .union([z.coerce.number().min(0, "Must be positive"), z.literal("")])
      .optional()
      .transform((v) => (v === "" || v === undefined ? undefined : v)),
    salary_max: z
      .union([z.coerce.number().min(0, "Must be positive"), z.literal("")])
      .optional()
      .transform((v) => (v === "" || v === undefined ? undefined : v)),
    currency: z.string().length(3, "Use a 3-letter code e.g. ETB"),
    location: z.string().max(255).optional().or(z.literal("")),
    is_remote: z.boolean(),
    application_deadline: z
      .string()
      .optional()
      .or(z.literal(""))
      .refine(
        (v) =>
          !v ||
          new Date(v).getTime() > Date.now() ||
          Number.isNaN(new Date(v).getTime()),
        "Deadline must be in the future"
      ),
    category: z.string().max(100).optional().or(z.literal("")),
    tags: z.string().optional().default(""),
  })
  .refine(
    (data) =>
      data.salary_min === undefined ||
      data.salary_max === undefined ||
      data.salary_min <= data.salary_max,
    {
      message: "Minimum salary must be less than or equal to maximum salary",
      path: ["salary_max"],
    }
  );

export type JobFormValues = z.input<typeof jobSchema>;
export type JobFormOutput = z.output<typeof jobSchema>;

/** Convert newline/comma separated textarea input to string arrays for the API. */
export function splitLines(value?: string): string[] {
  if (!value) return [];
  return value
    .split(/\r?\n|,(?![^(]*\))/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export const companyProfileSchema = z.object({
  name: z.string().min(1, "Company name is required").max(255),
  description: z.string().max(5000).optional().or(z.literal("")),
  industry: z.string().max(100).optional().or(z.literal("")),
  city: z.string().max(100).optional().or(z.literal("")),
  country: z.string().max(100).optional().or(z.literal("")),
  address: z.string().max(255).optional().or(z.literal("")),
});
export type CompanyProfileFormValues = z.infer<typeof companyProfileSchema>;
