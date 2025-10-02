import os
import pandas as pd
from datetime import datetime, timedelta
from calendar import month_name
from crypto_utils import load_key, ensure_encrypted_backup, safe_decrypt_file, safe_temp_file
from settings import config

class AttendanceRegister:
    def __init__(self):
        self.excel_file = config.excel_file
        self.yearly_file = config.yearly_file
        self.master_file = config.master_file
        self.calendar_file = config.calendar_file
        self.today = datetime.now().date()
        self.today_str = self.today.isoformat()
        self.key = load_key()

        self._ensure_register()
        self._ensure_yearly()
        self._ensure_master()
        self._ensure_calendar()

    # ---------------- Daily Register ----------------
    def _ensure_register(self):
        if not os.path.exists(self.excel_file):
            df = pd.DataFrame(columns=["StudentID", "Name", self.today_str])
            df.to_excel(self.excel_file, index=False)
        else:
            tmp_path = safe_temp_file()
            try:
                safe_decrypt_file(self.excel_file, self.key, dst_path=tmp_path)
                df = pd.read_excel(tmp_path)
                if self.today_str not in df.columns:
                    df[self.today_str] = 'A'
                    df.to_excel(self.excel_file, index=False)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        ensure_encrypted_backup(self.excel_file, self.key)

    # ---------------- Yearly Register ----------------
    def _ensure_yearly(self):
        if not os.path.exists(self.yearly_file):
            months = [m[:3] for m in month_name if m]
            df = pd.DataFrame(columns=["StudentID", "Name", "JoinDate"] + months + ["Total%", "Total_Present", "Total_Absent"])
            df.to_excel(self.yearly_file, index=False)
        ensure_encrypted_backup(self.yearly_file, self.key)

    # ---------------- Master Register ----------------
    def _ensure_master(self):
        if not os.path.exists(self.master_file):
            df = pd.DataFrame(columns=["StudentID", "Name", "Date", "Status"])
            df.to_excel(self.master_file, index=False)
        ensure_encrypted_backup(self.master_file, self.key)

    # ---------------- Calendar Register ----------------
    def _ensure_calendar(self):
        year = self.today.year
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)
        dates = [(start + timedelta(days=i)).date().isoformat() for i in range((end - start).days + 1)]
        expected_cols = ["StudentID", "Name"] + dates

        if not os.path.exists(self.calendar_file):
            df = pd.DataFrame(columns=expected_cols)
            df.to_excel(self.calendar_file, index=False)
        else:
            tmp_path = safe_temp_file()
            try:
                safe_decrypt_file(self.calendar_file, self.key, dst_path=tmp_path)
                df = pd.read_excel(tmp_path)

                # Add missing date columns
                missing_cols = [c for c in expected_cols if c not in df.columns]
                if missing_cols:
                    df_new_cols = pd.DataFrame('A', index=df.index, columns=missing_cols)
                    df = pd.concat([df, df_new_cols], axis=1)

                # Reorder columns
                df = df[expected_cols]

                # Remove duplicates
                df = df.drop_duplicates(subset=["StudentID", "Name"], keep="first")

                df.to_excel(self.calendar_file, index=False)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        ensure_encrypted_backup(self.calendar_file, self.key)

    # ---------------- Normalize Schemas ----------------
    def _normalize_schemas(self):
        """Ensure master file has correct columns."""
        master_cols = ["StudentID", "Name", "Date", "Status"]
        if os.path.exists(self.master_file):
            try:
                dfm = pd.read_excel(self.master_file)
                for col in master_cols:
                    if col not in dfm.columns:
                        dfm[col] = ''
                dfm = dfm[master_cols]
                dfm.to_excel(self.master_file, index=False)
            except Exception:
                pd.DataFrame(columns=master_cols).to_excel(self.master_file, index=False)

    # ---------------- Add Student ----------------
    def add_student(self, student_id, name):
        self._ensure_register()
        df = pd.read_excel(self.excel_file)
        if student_id not in df["StudentID"].values:
            cols = list(df.columns)
            row = {c: 'A' for c in cols}
            row["StudentID"] = student_id
            row["Name"] = name
            df = pd.concat([df, pd.DataFrame([row], columns=cols)], ignore_index=True)
            df.to_excel(self.excel_file, index=False)
            ensure_encrypted_backup(self.excel_file, self.key)

        self._ensure_yearly()
        yf = pd.read_excel(self.yearly_file)
        if student_id not in yf.get("StudentID", pd.Series(dtype=object)).values:
            months = [m[:3] for m in month_name if m]
            row = {"StudentID": student_id, "Name": name, "JoinDate": self.today_str}
            for m in months:
                row[m] = 0.0
            row["Total%"] = 0.0
            row["Total_Present"] = 0
            row["Total_Absent"] = 0
            yf = pd.concat([yf, pd.DataFrame([row])], ignore_index=True)
            yf.to_excel(self.yearly_file, index=False)
            ensure_encrypted_backup(self.yearly_file, self.key)

        self._ensure_calendar()
        cf = pd.read_excel(self.calendar_file)
        if student_id not in cf["StudentID"].values:
            new_row = {"StudentID": student_id, "Name": name}
            for c in cf.columns:
                if c not in ["StudentID", "Name"]:
                    new_row[c] = 'A'
            cf = pd.concat([cf, pd.DataFrame([new_row], columns=cf.columns)], ignore_index=True)
            cf.to_excel(self.calendar_file, index=False)
            ensure_encrypted_backup(self.calendar_file, self.key)

    # ---------------- Mark Attendance ----------------
    def mark_attendance(self, student_id, name, status="P"):
        """Mark attendance for a student and update all Excel files."""
        try:
            print(f"[DEBUG] Marking attendance for {name} (ID: {student_id}) - Status: {status}")
            print(f"[DEBUG] Excel file path: {self.excel_file}")
            print(f"[DEBUG] Today's date: {self.today_str}")
            
            # Ensure student exists
            self.add_student(student_id, name)
            
            # Update daily register
            if not os.path.exists(self.excel_file):
                print(f"[DEBUG] Creating new Excel file: {self.excel_file}")
                df = pd.DataFrame(columns=["StudentID", "Name", self.today_str])
            else:
                df = pd.read_excel(self.excel_file)
                print(f"[DEBUG] Loaded Excel with {len(df)} rows")
            
            if self.today_str not in df.columns:
                df[self.today_str] = 'A'
                print(f"[DEBUG] Added today's column: {self.today_str}")
            
            # Update attendance for the student
            student_mask = df["StudentID"] == student_id
            if student_mask.any():
                df.loc[student_mask, self.today_str] = status
                print(f"[DEBUG] Updated existing student {student_id}")
            else:
                # Add new student row if not found
                new_row = {col: 'A' for col in df.columns}
                new_row["StudentID"] = student_id
                new_row["Name"] = name
                new_row[self.today_str] = status
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                print(f"[DEBUG] Added new student {student_id}")
            
            # Save daily register
            df.to_excel(self.excel_file, index=False)
            print(f"[DEBUG] Saved Excel file: {self.excel_file}")
            ensure_encrypted_backup(self.excel_file, self.key)

            # Update other registers
            self._update_master(student_id, name, status)
            self._update_calendar(student_id, status)
            self._update_yearly(student_id)
            
            print(f"[SUCCESS] Attendance marked successfully for {name}")
            
        except Exception as e:
            print(f"[ERROR] Error marking attendance: {e}")
            import traceback
            traceback.print_exc()
            # Try to save at least the daily register
            try:
                if os.path.exists(self.excel_file):
                    df = pd.read_excel(self.excel_file)
                    if self.today_str not in df.columns:
                        df[self.today_str] = 'A'
                    student_mask = df["StudentID"] == student_id
                    if student_mask.any():
                        df.loc[student_mask, self.today_str] = status
                        df.to_excel(self.excel_file, index=False)
                        print(f"[FALLBACK] Saved basic attendance for {name}")
            except Exception as fallback_error:
                print(f"[FALLBACK ERROR] {fallback_error}")

    # ---------------- Master Update ----------------
    def _update_master(self, student_id, name, status):
        tmp_path = safe_temp_file()
        try:
            safe_decrypt_file(self.master_file, self.key, dst_path=tmp_path)
            df = pd.read_excel(tmp_path)

            mask = (df['StudentID'] == student_id) & (df['Date'] == self.today_str)
            if mask.any():
                df.loc[mask, 'Status'] = status
            else:
                new_row = {"StudentID": student_id, "Name": name, "Date": self.today_str, "Status": status}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            df.to_excel(self.master_file, index=False)
            ensure_encrypted_backup(self.master_file, self.key)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ---------------- Calendar Update ----------------
    def _update_calendar(self, student_id, status):
        tmp_path = safe_temp_file()
        try:
            safe_decrypt_file(self.calendar_file, self.key, dst_path=tmp_path)
            df = pd.read_excel(tmp_path)

            if self.today_str not in df.columns:
                df[self.today_str] = 'A'
            df.loc[df["StudentID"] == student_id, self.today_str] = status

            df.to_excel(self.calendar_file, index=False)
            ensure_encrypted_backup(self.calendar_file, self.key)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ---------------- Yearly Update ----------------
    def _update_yearly(self, student_id):
        tmp_daily = safe_temp_file()
        tmp_yearly = safe_temp_file()
        try:
            # Read daily and yearly files safely
            safe_decrypt_file(self.excel_file, self.key, dst_path=tmp_daily)
            daily_df = pd.read_excel(tmp_daily)

            safe_decrypt_file(self.yearly_file, self.key, dst_path=tmp_yearly)
            yf = pd.read_excel(tmp_yearly)

            months = [m[:3] for m in month_name if m]
            idx_list = yf.index[yf["StudentID"] == student_id].tolist()
            if not idx_list:
                return
            idx = idx_list[0]

            join_date = yf.loc[idx, "JoinDate"]
            join_date = datetime.fromisoformat(str(join_date)).date() if pd.notna(join_date) else None

            month_totals = {m: 0 for m in months}
            month_present = {m: 0 for m in months}

            for col in daily_df.columns[2:]:
                try:
                    col_date = datetime.fromisoformat(col).date()
                except Exception:
                    continue
                if join_date and col_date < join_date:
                    continue
                month_abbr = col_date.strftime("%b")
                val = str(daily_df.loc[daily_df["StudentID"] == student_id, col].values[0]).strip().upper()
                month_totals[month_abbr] += 1
                if val == "P":
                    month_present[month_abbr] += 1

            total_present = sum(month_present.values())
            total_days = sum(month_totals.values())

            for m in months:
                yf.loc[idx, m] = round((month_present[m] / month_totals[m]) * 100, 2) if month_totals[m] > 0 else 0.0
            yf.loc[idx, "Total%"] = round((total_present / total_days) * 100, 2) if total_days > 0 else 0.0
            yf.loc[idx, "Total_Present"] = total_present
            yf.loc[idx, "Total_Absent"] = total_days - total_present

            yf.to_excel(self.yearly_file, index=False)
            ensure_encrypted_backup(self.yearly_file, self.key)
        finally:
            for tmp_file in [tmp_daily, tmp_yearly]:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)

    # ---------------- Reset ----------------
    def reset_all(self):
        for f in [self.excel_file, self.yearly_file, self.master_file, self.calendar_file]:
            if os.path.exists(f):
                os.remove(f)
        self._ensure_register()
        self._ensure_yearly()
        self._ensure_master()
        self._ensure_calendar()
